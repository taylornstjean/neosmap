import numpy as np
from config import MONITOR_TIME_INTERVAL, MPC_NEO_KEY_MAP, DATA_SUBDIRS, CACHE_USER_DIR
from flask_login import current_user
from neosmap.core.data.base import NEOMonitorBase
import os
import json
from neosmap.core.caching import APICache
from neosmap.core.api import retrieve_data_mpc
from neosmap.logger import logger
from datetime import datetime as dt
from dataclasses import dataclass, asdict
import pandas as pd


###########################################################################
# DEFINE NEO MONITOR AND NEO MONITOR DAEMON CLASS

class NEOMonitor(NEOMonitorBase):
    """Stores an access pointer to monitoring data for each user. Data is routinely updated by a backend process."""

    def __init__(self, user, *args, **kwargs):
        super(NEOMonitorBase, self).__init__(*args, **kwargs)

        self._ignore_id_path = os.path.join(CACHE_USER_DIR, "{}_ignore_ids.json".format(current_user.id))
        self._user_model = user
        self.save_time = 12 * 3600  # 12 hours
        self._updates_path = os.path.join(DATA_SUBDIRS["monitor"], "updates.json")
        self.time_interval = MONITOR_TIME_INTERVAL
        self._update_occurred = False
        self._updates = []

    def get_ignore_ids(self, timestamp: bool = False) -> list | dict:
        """Retrieve the list of update IDs that have been ignored.

        :param timestamp: If True, the timestamp will be included and the function will return a dict.
        :type timestamp: bool
        """
        try:
            # load from user file
            with open(self._ignore_id_path, "r") as f:
                data = json.load(f)
                if not timestamp:
                    return [entry["id"] for entry in data]

                return data

        except FileNotFoundError:
            # nothing has been ignored by user
            return []

        except json.JSONDecodeError:
            # the file is corrupt, reset it
            with open(self._ignore_id_path, "w") as f:
                json.dump([], f)
            return []

    def save_ignore_ids(self, ids):
        """Ignore a list of update IDs for this user.

        :param ids: List of update IDs to clear.
        :type ids: list
        """
        current_time = dt.utcnow().timestamp()
        data = self.get_ignore_ids(timestamp=True)

        for _id in ids:
            data.append({"id": _id, "ts": current_time})

        with open(self._ignore_id_path, "w") as f:
            json.dump(data, f, indent=4)

    def _clean_ignore_ids(self):
        """Clean the list of ignored update IDs for this user. Deletes expired update IDs and
        IDs not in the update list."""
        data = self.get_ignore_ids(timestamp=True)

        current_time = dt.utcnow().timestamp()
        current_ids = [update["id"] for update in self._updates]

        to_delete = []
        for i, entry in enumerate(data):
            if (current_time - entry["ts"]) >= self.save_time:
                # update is expired, delete it
                to_delete.append(i)

            elif entry["id"] not in current_ids:
                # update does not exist
                to_delete.append(i)

        # remove IDs queued for deletion
        for i in sorted(to_delete, reverse=True):
            del data[i]

        with open(self._ignore_id_path, "w") as f:
            json.dump(data, f, indent=4)

    def remove_ignore_ids(self, ids):
        """Reinstate a list of update IDs for this user.

        :param ids: List of update IDs to recover.
        :type ids: list
        """
        data = self.get_ignore_ids(timestamp=True)
        filtered_data = [entry for entry in data if entry["id"] not in ids]

        with open(self._ignore_id_path, "w") as f:
            json.dump(filtered_data, f, indent=4)

    def sort_by_ignored(self, df):
        self._clean_ignore_ids()
        ignore_ids = self.get_ignore_ids()
        try:
            df["old"] = np.where(df["id"].isin(ignore_ids), "true", "false")
        except KeyError:
            pass
        return df

    @property
    def data(self):
        self.load_record()
        logger.debug("NEO Monitor data loaded successfully")
        _data = {
            "df": self._load_last_df(),
            "updates": pd.DataFrame(self._updates)
        }
        return _data


class NEOMonitorDaemon(NEOMonitorBase):
    """NEO Monitor daemon class for use by the backend daemon thread."""

    @dataclass
    class Entry:
        id: str
        banner: str
        action: str
        objectName: str
        time: str
        attribute: str = "none"
        nObs_i: str = "none"
        nObs_f: str = "none"

        def dict(self):
            return {k: str(v) for k, v in asdict(self).items()}

    def __init__(self, app, user, *args, **kwargs):
        super(NEOMonitorBase, self).__init__(*args, **kwargs)

        self._updates_path = os.path.join(DATA_SUBDIRS["monitor"], "updates.json")
        self._user_model = user
        self.save_time = 12 * 3600  # 12 hours
        self._app = app
        self.time_interval = MONITOR_TIME_INTERVAL
        self._update_occurred = False
        self._updates = []

    def _update(self, first_pull=False) -> None:

        logger.debug(f"Running update for NEO Monitor data (first_pull={first_pull})")

        def _retrieve_data():
            logger.debug("Retrieving data from MPC API")
            loaded_data = retrieve_data_mpc()
            return loaded_data

        data = _retrieve_data()

        logger.debug("Successfully retrieved data from MPC API")

        # Parsing and formatting data
        data_table = []
        for entry in data:
            parsed_entry = self._entry_parser(entry)
            if parsed_entry:
                data_table.append(parsed_entry)

        self._DF = pd.DataFrame(np.array(data_table), columns=MPC_NEO_KEY_MAP.values())

        if not first_pull:
            self._check_changes()

        cache_ = APICache(name="monitor", cache_type="monitor", cache_time=50)
        cache_.save(data_table)

    def check_update(self) -> None:
        logger.debug("Checking for updates to NEO Monitor data")

        try:
            _cache = APICache.get_instance(name="monitor")
            update_required = not _cache.valid or not _cache.verify
            first_pull = not _cache.verify
            logger.debug("Found cached NEO Monitor data")

        except ValueError:
            update_required = True
            first_pull = True

        if update_required:
            self._update(first_pull=first_pull)
        else:
            self._update_occurred = False
            self.load_record()

        if self._update_occurred:
            logger.debug("Update occurred, activating ping")

            self._user_model.activate_ping(self._app)

    def _check_changes(self) -> None:

        logger.debug("Checking for changes to stored NEO Monitor data from new data")

        _DF_last = self._load_last_df()

        try:
            diff_df = pd.merge(
                _DF_last.objectName, self._DF.objectName, indicator=True, how="outer"
            ).loc[lambda x: x["_merge"] != 'both']
        except pd.errors.MergeError:
            diff_df = pd.DataFrame()

        new_objects = diff_df[diff_df["_merge"] == "right_only"]["objectName"]
        removed_objects = diff_df[diff_df["_merge"] == "left_only"]["objectName"]

        _changes = new_objects.to_list() + removed_objects.to_list()

        _DF_last_trim = _DF_last.loc[~_DF_last["objectName"].isin(_changes)]
        _DF_trim = self._DF.loc[~self._DF["objectName"].isin(_changes)]

        _nobs_merge_cols = ["objectName", "nObs"]

        try:
            diff_df_nobs = pd.merge(
                _DF_last_trim[_nobs_merge_cols], _DF_trim[_nobs_merge_cols],
                how="outer", suffixes=("_i", "_f"), on="objectName"
            ).loc[lambda x: x["nObs_i"] != x["nObs_f"]]
        except pd.errors.MergeError:
            diff_df_nobs = pd.DataFrame()

        alter_nobs_objects = diff_df_nobs

        if any(df.shape[0] >= 1 for df in [new_objects, removed_objects, alter_nobs_objects]):
            self._update_occurred = True
            logger.debug("Changes to NEO Monitor data were detected")
        else:
            logger.debug("No changes to NEO Monitor data were detected")
            self._update_occurred = False

        current_time = dt.utcnow()
        current_time_frmt = current_time.strftime("%b %d  %H:%M")

        def _id(obj, act, time):
            return "{}-{}-{}".format(obj, act, time)

        self.load_record()

        for object_ in removed_objects.to_list():
            entry_id = _id(object_, "remove", int(current_time.timestamp()))
            entry = self.Entry(banner="Object Removed", action="object-removal", objectName=object_, id=entry_id,
                               time=current_time_frmt)
            self._updates.insert(0, entry.dict())

        for object_ in new_objects.to_list():
            entry_id = _id(object_, "add", int(current_time.timestamp()))
            entry = self.Entry(banner="Object Added", action="object-addition", objectName=object_, id=entry_id,
                               time=current_time_frmt)
            self._updates.insert(0, entry.dict())

        for update in alter_nobs_objects.to_dict(orient="index").values():
            entry_id = _id(update["objectName"], "nobs", int(current_time.timestamp()))
            entry = self.Entry(banner="Object Updated", action="object-alter", objectName=update["objectName"],
                               id=entry_id, attribute="nobs", nObs_i=update["nObs_i"], nObs_f=update["nObs_f"],
                               time=current_time_frmt)
            self._updates.insert(0, entry.dict())

        self._update_record()

    def _update_record(self):
        logger.debug("Updating NEO Monitor record")
        self._clean_record()
        with open(self._updates_path, "w") as f:
            json.dump(self._updates, f)

    def _clean_record(self):
        logger.debug("Cleaning NEO Monitor record")
        to_delete = []
        for i, entry in enumerate(self._updates):
            _id = entry["id"]
            entry_time = float(_id.split("-")[-1])
            current_time = dt.utcnow().timestamp()

            if (current_time - entry_time) > self.save_time:
                to_delete.append(i)

        for i in sorted(to_delete, reverse=True):
            del self._updates[i]


# ------------------------------ END OF FILE ------------------------------
