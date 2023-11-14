from datetime import datetime
from datetime import timedelta
from config import DATA_SUBDIRS, JPL_API_URL, EPH_TIME_INCR, OBS_TIME
from neosmap.logging import ephemeris_log_save, ephemeris_last_save
from .exceptions import TdesNotFoundError, EphemerisParamsNotSetError, OutdatedParamsError
from datetime import datetime as dt
import os
import json
import requests


###########################################################################
# DEFINE EPHEMERIS CLASS

class Ephemeris:

    def __init__(self, tdes):
        self._params = {"tdes": tdes}
        self._session = requests.Session()

    def set_params(self, defaults=False, **kwargs) -> None:
        """Sets parameters for API fetch."""

        if defaults:
            self._params["eph-start"] = dt.utcnow().strftime("%Y-%m-%d_%X")
            self._params["eph-stop"] = (dt.utcnow() + timedelta(hours=OBS_TIME)).strftime("%Y-%m-%d_%X")
            self._params["eph-step"] = str(EPH_TIME_INCR) + "m"
        else:
            eph_start = kwargs.get("eph_start")
            eph_stop = kwargs.get("eph_stop")
            eph_step = kwargs.get("eph_step")
            eph_step_unit = kwargs.get("eph_step_unit", "m")

            self._params["eph-start"] = eph_start.strftime("%Y-%m-%d_%X")
            self._params["eph-stop"] = eph_stop.strftime("%Y-%m-%d_%X")
            self._params["eph-step"] = str(eph_step) + eph_step_unit

    def get_single_ephemeris(self, eph_start) -> dict:
        temp_session = requests.Session()
        local_params = {"tdes": self._params["tdes"], "eph-start": eph_start.strftime("%Y-%m-%d_%X")}

        url_base = JPL_API_URL
        data = temp_session.get(url_base, params=local_params)
        json_data = json.loads(data.content)

        try:
            ephemeris = json_data["eph"]
        except KeyError:
            if json_data["error"] == "specified object does not exist":
                raise TdesNotFoundError(field=self._params["tdes"])
            else:
                raise KeyError

        del temp_session
        return ephemeris

    def get_data(self):
        self._check_currency()
        self.check_update()
        return self._data

    def _check_currency(self):
        if hasattr(self, "_data"):
            timestr_eph = self._data[0]["time"]
            datetime_eph = datetime.strptime(timestr_eph, "%Y-%m-%d %X")

            timestamp_eph = datetime_eph.timestamp()
            timestamp_now = datetime.utcnow().timestamp()

            save_buffer = 1800  # seconds

            if (timestamp_now - timestamp_eph) >= save_buffer:
                try:
                    os.remove(os.path.join(DATA_SUBDIRS["ephemerides"], f"{self._params['tdes']}.json"))
                except FileNotFoundError:
                    pass
                raise OutdatedParamsError

    def check_update(self, force_update=False):
        """Update stored ephemeris data if necessary.

        :param force_update: If True, overrides data currency checks and forces an update. Defaults to False.
        :type force_update: bool
        """

        save_buffer = 1800  # seconds

        last_save = ephemeris_last_save(self._params["tdes"])
        update_required = bool(dt.utcnow().timestamp() - last_save >= save_buffer) if last_save else True

        if not os.path.isfile(
                os.path.join(DATA_SUBDIRS["ephemerides"], f"{self._params['tdes']}.json")
        ) or update_required or force_update:
            self._update()
        elif not hasattr(self, "_data"):
            self._load()

    def _update(self):
        url_base = JPL_API_URL
        data = self._session.get(url_base, params=self._params)
        json_data = json.loads(data.content)

        try:
            self._data = json_data["eph"]
        except KeyError:
            try:
                if json_data["error"] == "specified object does not exist":
                    raise TdesNotFoundError(field=self._params["tdes"])
            except KeyError:
                for param in ["eph-start", "eph-stop", "eph-step"]:
                    try:
                        self._params[param]
                    except KeyError:
                        raise EphemerisParamsNotSetError

        for i in self._data:
            del i["data"]

        self._save()

    def _save(self):
        with open(os.path.join(DATA_SUBDIRS["ephemerides"], f"{self._params['tdes']}.json"), "w") as f:
            f.write(json.dumps(self._data, indent=4))
        ephemeris_log_save(self._params["tdes"])

    def _load(self):
        try:
            with open(os.path.join(DATA_SUBDIRS["ephemerides"], f"{self._params['tdes']}.json"), "r") as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._update()

# ------------------------------ END OF FILE ------------------------------
