"""This scripting algorithm is specific to telescopes running on ACP Observatory Control Software."""

from .imaging import Image
from astropy import units as u
from collections import namedtuple
from datetime import datetime as dt
from datetime import timedelta
from neosmap.core.exceptions import ImageCountExceededError
import os
from config import TEMP_SUBDIRS


class Script:

    # Define directive sequence struct
    _script_directive_attrs = "count interval binning filter_name autofocus tdes ra dec"
    _directiveSequence = namedtuple(
        "_directiveSequence",
        _script_directive_attrs
    )

    # Formatting
    _datetime_strf = "%d-%b-%Y %H:%M:%S"

    def __init__(self, **kwargs):

        # Object data
        self._neo_data = kwargs.get("neo_data")
        self._observatory = kwargs.get("observatory")
        self._tdes = kwargs.get("tdes")

        # Imaging params
        self._filter_name = kwargs.get("filter_name", "bg40")
        self._binning = int(kwargs.get("binning", 2))
        self._interval = int(kwargs.get("exposure_time", 60))
        self._count = int(kwargs.get("count", 1))
        self._autofocus = kwargs.get("autofocus", True)

        # Imaging options
        self._image_delay = int(kwargs.get("image_delay", 900))
        self._observe_start = kwargs.get("observe_start")
        self._blink_count = int(kwargs.get("blink_count", 3))

        # Initialize directive stack
        self._directive_stack = {}

        if self._observe_start == "" or not self._observe_start:
            self._observe_start = dt.utcnow() + timedelta(seconds=900)
        if isinstance(self._observe_start, str):
            self._observe_start = dt.strptime(self._observe_start, "%Y-%m-%dT%H:%M")

    def _get_ephemerides(self):
        data = self._neo_data.ephemerides(self._tdes).get_single_ephemeris(self._observe_start)[0]
        return data

    def generate_script(self):
        eph_data = self._get_ephemerides()

        uncertainty = (float(eph_data["sigma-pos"]) * u.arcmin).to(u.deg).value
        image_overlap = 0.05

        imaging_area = (uncertainty * 2, uncertainty * 2 if uncertainty < 45 else 90)
        center_coord = (float(eph_data["median"]["ra"]), float(eph_data["median"]["dec"]))

        image = Image(self._observatory, imaging_area, self._observe_start, center_coord, image_overlap)
        image_coords = image.get_imaging_coords()

        max_images = 9
        if len(image_coords) > max_images:
            raise ImageCountExceededError(
                f"Image count of {len(image_coords)} exceeds max image per NEO limit of {max_images}. Uncertainty may "
                f"be too high."
            )

        for d_set in range(self._blink_count):
            self._directive_stack[d_set] = []
            for coord in image_coords:
                self._directive_stack[d_set].append(
                    self._directiveSequence(
                        count=self._count,
                        interval=self._interval,
                        binning=self._binning,
                        filter_name=self._filter_name,
                        autofocus=self._autofocus,
                        tdes=self._tdes,
                        ra=coord[0],
                        dec=coord[1]
                    )
                )

        self._compile()

    def _compile(self):
        file_payload = "?\n? Script generated using NEOSMAP on {}\n?\n\n".format(dt.utcnow().strftime("%c"))
        entry_template = "".join(["{}" for _ in range(len(self._script_directive_attrs.split(" ")) - 2)])

        for d_set, directives in self._directive_stack.items():
            wait_until = (
                    self._observe_start + timedelta(seconds=int(d_set) * self._image_delay)
            ).strftime(self._datetime_strf)

            file_payload += "#WAITUNTIL %d, %s\n\n" % (d_set + 1, wait_until)
            file_payload += "#SETS %d\n\n" % (int(d_set) + 1)
            for d in directives:
                entry = entry_template.format(
                    "#COUNT %d\n" % d.count,
                    "#INTERVAL %d\n" % d.interval,
                    "#BINNING %d\n" % d.binning,
                    "#FILTER %s\n" % d.filter_name,
                    "#AUTOFOCUS\n" if d.autofocus else "",
                    "%s\t%f\t%f\n\n" % (d.tdes, d.ra, d.dec)
                )

                file_payload += entry

        with open(os.path.join(TEMP_SUBDIRS["script"], f"{self._tdes}-observation.txt"), 'w') as f:
            f.writelines(file_payload)
