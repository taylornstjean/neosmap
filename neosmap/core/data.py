import numpy as np
from numpy import ndarray
from pandas import DataFrame
import operator
from functools import partial, lru_cache
from config import (
    DATA_SUBDIRS,
    COLUMNS,
    FILTERABLE_COLS,
    JPL_API_URL
)
from neosmap.logging import neocp_last_save, neocp_log_save, clean_logs
from datetime import datetime as dt
from urllib.request import urlretrieve
import os
import json
from astropy import units as u
from astropy.units import Quantity
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from astropy.time import Time
import pandas as pd
from typing import Union
from collections import defaultdict
from .ephemerides import Ephemeris

neocp_json_path = os.path.join(DATA_SUBDIRS["neocp"], "neocp.json")


###########################################################################
# DEFINE OBSERVATORY CLASS

class Observatory:
    """A class that stores attributes related to the location of the observatory. Takes in a longitude, latitude,
    primary mirror diameter, telescope focal ratio and a minimum observation altitude.

    :param longitude: The longitudinal coordinates of the observatory.
    :type longitude: astropy.units.Quantity

    :param latitude: The latitudinal coordinates of the observatory.
    :type latitude: astropy.units.Quantity

    :param ts_mirror_diameter: The diameter of the telescope primary mirror.
    :type ts_mirror_diameter: astropy.units.Quantity

    :param ts_focal_ratio: The focal number of the telescope (for format f/#, use #).
    :type ts_focal_ratio: float | int

    :param min_altitude: The minimum observation altitude of the observatory.
    :type min_altitude: astropy.units.Quantity
    """

    def __init__(
            self,
            longitude: Quantity[u.degree],
            latitude: Quantity[u.degree],
            ts_mirror_diameter: Quantity[u.m],
            ts_focal_ratio: Union[float, int],
            min_altitude: Quantity[u.degree]
    ) -> None:
        self.longitude = longitude
        self.latitude = latitude
        self.ts_mirror_diameter = ts_mirror_diameter
        self.ts_focal_ratio = ts_focal_ratio
        self.min_altitude = min_altitude
        self.location = EarthLocation.from_geodetic(lat=latitude, lon=longitude)

    def get_sidereal_time(self):
        """Returns local sidereal time at the observatory."""

        observing_time = Time(dt.utcnow(), scale='utc', location=self.location)
        sidereal = observing_time.sidereal_time('mean')
        return sidereal

    @property
    def afov(self) -> Quantity[u.rad]:
        """Returns the angular field of view of the observatory telescope in degrees."""

        focal_length = self.ts_focal_ratio * self.ts_mirror_diameter
        afov = 2 * np.arctan(self.ts_mirror_diameter / (2 * focal_length))
        return afov.value * u.degree

    def check_visibility(self, ra, dec, observe_time: Time):
        altaz = AltAz(location=self.location, obstime=observe_time)
        radec = SkyCoord(ra, dec, frame="icrs", unit=u.deg)
        obj_obs = radec.transform_to(altaz)

        obj_vis = bool(obj_obs.alt >= self.min_altitude)

        return obj_vis


###########################################################################
# DEFINE NEODATA CLASS

class NEOData:

    def __init__(self, observatory) -> None:
        """Initializes an instance that contains up-to-date NEOCP data. Also maintains
         a reference to an ephemeris object for each NEO.

         :param observatory: Observatory object.
         :type observatory: neosmap.core.Observatory
         """

        self._observatory = observatory

        self.check_update()
        self._clean_ephemeris_saves()
        clean_logs(self)

    # ================================================================
    # TDES CHECK

    def is_valid_designation(self, tdes: Union[str, list]) -> bool:
        # -----  UNUSED  ----- #

        """Checks if ``tdes`` is a valid temporary designation to an existing NEO.

        :param tdes: Temporary designation(s) to verify. If multiple temporary designations are passed as a list,
            this function will return ``True`` only if all temporary designations are valid.
        :type tdes: list, str
        """

        tdes = [tdes] if isinstance(tdes, str) else tdes
        exist = list(map(lambda x: x in self._DF["objectName"].values, tdes))
        return all(exist)

    # ================================================================
    # UPDATE

    def _update(self, use_cache=False) -> None:
        """Updates NEOCP data."""

        def _retrieve_data():
            urlretrieve(JPL_API_URL, neocp_json_path)
            neocp_log_save()

        if not use_cache:
            _retrieve_data()

        with open(neocp_json_path, 'r') as f:
            try:
                data = json.load(f)
                retrieve_required = False
            except json.decoder.JSONDecodeError:
                retrieve_required = True

        if retrieve_required:
            _retrieve_data()
            with open(neocp_json_path, 'r') as f:
                data = json.load(f)

        # Parsing and formatting data
        data_table = []
        for entry in data["data"]:
            parsed_entry = self._entry_parser(entry)
            data_table.append(parsed_entry)

        self._array = np.array(data_table)
        self._DF = pd.DataFrame(self._array, columns=COLUMNS)
        self._create_ephemeris_instance()

    def check_update(self, force_update=False) -> None:
        """Update stored NEO data if necessary.

        :param force_update: If ``True``, overrides data currency checks and forces an update. Defaults to ``False``.
        :type force_update: bool
        """

        save_buffer = 1800  # seconds

        last_save = neocp_last_save()
        update_required = bool(dt.utcnow().timestamp() - last_save >= save_buffer) if last_save else True

        if (
            not os.path.isfile(neocp_json_path)
            or bool(update_required)
            or force_update
        ):
            self._update()
        elif not hasattr(self, "_DF"):
            self._update(use_cache=True)
        else:
            self._create_ephemeris_instance()

    # ================================================================
    # EPHEMERIDES

    def _create_ephemeris_instance(self) -> None:
        """Initializes ephemeris instances from class Ephemeris for each NEO."""

        if not hasattr(self, "_DF"):
            self.check_update()

        if not hasattr(self, "_ephemerides"):
            self._ephemerides = {}
            for tdes in self._DF["objectName"]:
                self._ephemerides[tdes] = Ephemeris(tdes=tdes)
        else:
            # Add undefined tdes Ephemeris objects
            for tdes in self._DF["objectName"]:
                if tdes not in self._ephemerides.keys():
                    self._ephemerides[tdes] = Ephemeris(tdes=tdes)

            # Remove Ephemeris objects for non-existent tdes
            to_delete = []
            for tdes in self._ephemerides.keys():
                if not (self._DF['objectName'].eq(tdes)).any():
                    to_delete.append(tdes)
            for tdes in to_delete:
                del self._ephemerides[tdes]

    def ephemerides(self, tdes):
        """Get ephemerides for specified tdes

        :param tdes: Specify one temporary designation.
        :type tdes: str
        """

        try:
            ephemeris = self._ephemerides[tdes]
        except KeyError:
            self.check_update()
            ephemeris = self._ephemerides[tdes]

        return ephemeris

    def _clean_ephemeris_saves(self):
        """Remove saved ephemeris data for non-existent temporary designations."""

        ephem_data_dir = DATA_SUBDIRS["ephemerides"]

        for file in os.listdir(ephem_data_dir):
            tdes = file.split(".")[0]
            if not (self._DF['objectName'].eq(tdes)).any():
                os.remove(os.path.join(ephem_data_dir, file))

    # ================================================================
    # DATA

    def _get_visibility(self, neo: dict) -> bool:
        ra_split = neo["ra"].split(":")
        ra_ha = (float(ra_split[0]) + (float(ra_split[1]) / 60))
        ra = ra_ha * u.hourangle
        dec = float(neo["dec"]) * u.degree
        observe_time = Time(dt.utcnow())
        obj_vis = self._observatory.check_visibility(ra, dec, observe_time)
        return obj_vis

    def df(
            self,
            cols: Union[str, list] = None,
            tdes: Union[str, list] = None,
            conditions: dict = None,
            sort_by_column: list = None,
            visible: bool = None,
            force_update: bool = None
    ):
        """
        Returns a Pandas DataFrame object with stored data. Updates stored NEO data if necessary.

        :param cols: Specify one or more columns to include. Defaults to all.
        :type cols: str, list

        :param tdes: Specify one or more temporary designations to include.
        :type tdes: str, list

        :param conditions: Provide conditions.
            Format: ``{column: {op: val}}`` where ``column`` is the column name the condition is applied to,
            ``op`` is the operation from ``["leq", "geq", "le", "ge", "eq"]`` and ``val`` is a float value.
            Supports specification of multiple op/val pairs per column.
        :type conditions: dict

        :param sort_by_column: Specify a column to sort by in descending order. Defaults to index.
        :type sort_by_column: list

        :param visible: ``True``: includes only visible objects. ``False``: includes all objects. Defaults to ``False``.
        :type visible: bool

        :param force_update: If ``True``, overrides data currency checks and forces an update. Defaults to ``False``.
        :type force_update: bool
        """

        self.check_update(force_update=force_update)

        data = self._DF

        tdes = [tdes] if tdes and isinstance(tdes, str) else tdes
        cols = ["objectName", cols] if cols and isinstance(cols, str) else ["objectName"] + cols if cols else cols

        # Row sort

        data = data.loc[data["objectName"].isin(tdes)] if tdes else data
        data = self._conditions(conditions, data) if conditions else data

        if sort_by_column in FILTERABLE_COLS:
            data.sort_values(sort_by_column, axis=0, inplace=True, ascending=False, key=lambda s: s.astype(float))

        # Column sort

        data = data.loc[data["vis"].astype(bool)] if visible else data
        data = data[cols] if cols else data

        return data.reset_index(drop=True)

    def get_array(self, force_update) -> ndarray:
        # -----  UNUSED  ----- #

        """Returns a Numpy array with all stored data. Updates stored NEO data if necessary."""

        self.check_update(force_update=force_update)
        return self._array

    # ================================================================
    # FULLSCORE ALGORITHM

    @staticmethod
    def _normal(x, max_x, min_x):
        score = np.exp(-((x - max_x) ** 2) / (2 * (np.abs(max_x - min_x) / 3) ** 2))
        return score

    @staticmethod
    def _cut_normal(x, max_x, stddev, max_diff):
        if np.abs(max_x - x) >= max_diff:
            return -1
        score = np.exp(-((x - max_x) ** 2) / (2 * stddev ** 2))
        return score

    @staticmethod
    def _skewed_normal(x, max_x, min_x_n, min_x_p):
        if x <= max_x:
            score = np.exp(-((x - max_x) ** 2) / (2 * (np.abs(max_x - min_x_n) / 3) ** 2))
        else:
            score = np.exp(-((x - max_x) ** 2) / (2 * (np.abs(max_x - min_x_p) / 3) ** 2))
        return score

    @staticmethod
    def _linear(x, min_x, max_x):
        score = (1 / (max_x - min_x)) * (x - min_x)
        return score

    @staticmethod
    def _hyperbolic(x, max_x, min_x):
        score = (np.tanh((2 * (x - max_x)) / (max_x - min_x)) + 1) / 2
        return score

    @lru_cache(maxsize=200)
    def _full_score(self, neo):
        latitude = self._observatory.latitude.value
        minimum_altitude = self._observatory.min_altitude.value
        afov = self._observatory.afov.to(u.arcsec)

        score_map = {
            "nObs": [partial(self._skewed_normal, max_x=10, min_x_n=0, min_x_p=30), 4],
            "arc": [partial(self._skewed_normal, max_x=1, min_x_n=0, min_x_p=4), 1],
            "neoScore": [partial(self._normal, max_x=80, min_x=100), 4],
            "tisserandScore": [partial(self._linear, max_x=0, min_x=100), 1],
            "geocentricScore": [partial(self._linear, max_x=0, min_x=100), 1],
            "phaScore": [partial(self._linear, max_x=100, min_x=0), 1],
            "dec": [partial(self._cut_normal, max_x=latitude, stddev=70, max_diff=90 - minimum_altitude), 10],
            "Vmag": [partial(self._hyperbolic, max_x=19, min_x=23), 10],
            "unc": [partial(self._skewed_normal, max_x=round(afov.value), min_x_n=0, min_x_p=800), 5]
        }

        total_score = 0
        norm = 0

        for col, (func, w) in score_map.items():
            value = neo[COLUMNS.index(col)]
            if func(x=value if value else 0) == -1:
                return 0
            total_score += func(x=value if value else 0) * w
            norm += w

        total_score /= norm * 0.01
        return round(total_score, 3)

    # ================================================================
    # MISC

    def _conditions(self, conditions, data) -> DataFrame:
        for col, filt in conditions.items():
            unpack_filt = {o: v for o, v in filt.items() if v != ""}
            for op_str, val in unpack_filt.items():
                operation = self._get_operator(op_str)
                data = data.loc[operation(data[col].astype(float), float(val))]
        return data

    @staticmethod
    def _get_operator(op_str):
        operators = defaultdict(
            lambda: operator.eq, {
                "eq": operator.eq,
                "ge": operator.ge,
                "le": operator.le,
                "gt": operator.gt,
                "lt": operator.lt
            }
        )
        return operators[op_str]

    def _entry_parser(self, entry):
        parsed = []
        for column in COLUMNS:
            if column in ["objectName", "tEphem", "lastRun"]:
                parsed.append(entry[column])
            elif column in ["ra"]:
                # Convert ra unit (original form hh:mm) to hour angle
                ra_split = entry[column].split(":")
                ra_ha = round(float(ra_split[0]) + (float(ra_split[1]) / 60), 2)
                parsed.append(ra_ha)
            elif column in ["vis"]:
                parsed.append(self._get_visibility(entry))
            elif column in ["fullScore"]:
                pass
            else:
                try:
                    parsed.append(float(entry[column]) if entry[column] else None)
                except KeyError:
                    parsed.append(np.nan)
        parsed.append(self._full_score(tuple(parsed)))
        return parsed

# ------------------------------ END OF FILE ------------------------------
