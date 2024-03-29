import numpy as np
from config import MONITOR_TIME_INTERVAL, MPC_NEO_KEY_MAP, DATA_SUBDIRS
from neosmap.core.caching import APICache
from neosmap.core.api import retrieve_data_mpc
from datetime import datetime as dt
from dataclasses import dataclass, asdict
import pandas as pd
import os
import json


class NEOMonitorBase:

    def __init__(self, user):

        self.time_interval = MONITOR_TIME_INTERVAL
        self.save_time = 12 * 3600  # 12 hours
        self._updates_path = os.path.join(DATA_SUBDIRS["monitor"], "updates.json")
        self._updates = []
        self._update_occurred = False
        self._user_model = user

    def _update(self, first_pull=False) -> None:

        def _retrieve_data():
            loaded_data = retrieve_data_mpc()
            return loaded_data

        data = _retrieve_data()

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

    @staticmethod
    def _entry_parser(entry):
        if not isinstance(entry, dict):
            return None

        parsed = []
        keys = [key for key in MPC_NEO_KEY_MAP.keys() if key != "vis"]
        for key in keys:
            parsed.append(entry[key])

        return parsed

    def check_update(self) -> None:
        try:
            _cache = APICache.get_instance(name="monitor")
            update_required = not _cache.valid or not _cache.verify
            first_pull = not _cache.verify

        except ValueError:
            update_required = True
            first_pull = True

        if update_required:
            self._update(first_pull=first_pull)
        else:
            self._update_occurred = False
            self._load_record()

        if self._update_occurred:
            self._user_model.activate_ping()

    def _load_last_df(self):
        cache_ = APICache.get_instance("monitor")
        data = cache_.load(ignore_cache_valid=True)

        data_table = []
        for entry in data:
            parsed_entry = self._entry_parser(entry)
            data_table.append(parsed_entry)

        return pd.DataFrame(np.array(data), columns=MPC_NEO_KEY_MAP.values())

    def _check_changes(self) -> None:

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
        else:
            self._update_occurred = False

        current_time = dt.utcnow()
        current_time_frmt = current_time.strftime("%b %d  %H:%M")

        def _id(obj, act, time):
            return "{}-{}-{}".format(obj, act, time)

        self._load_record()

        @dataclass
        class Entry:
            id: str
            banner: str
            action: str
            objectName: str
            time: float = current_time_frmt
            attribute: str = "none"
            nObs_i: str = "none"
            nObs_f: str = "none"

            def dict(self):
                return {k: str(v) for k, v in asdict(self).items()}

        for object_ in removed_objects.to_list():
            entry_id = _id(object_, "remove", int(current_time.timestamp()))
            entry = Entry(banner="Object Removed", action="object-removal", objectName=object_, id=entry_id)
            self._updates.insert(0, entry.dict())

        for object_ in new_objects.to_list():
            entry_id = _id(object_, "add", int(current_time.timestamp()))
            entry = Entry(banner="Object Added", action="object-addition", objectName=object_, id=entry_id)
            self._updates.insert(0, entry.dict())

        for update in alter_nobs_objects.to_dict(orient="index").values():
            entry_id = _id(update["objectName"], "nobs", int(current_time.timestamp()))
            entry = Entry(banner="Object Updated", action="object-alter", objectName=update["objectName"], id=entry_id,
                          attribute="nobs", nObs_i=update["nObs_i"], nObs_f=update["nObs_f"])
            self._updates.insert(0, entry.dict())

        self._update_record()

    def _update_record(self):
        self._clean_record()
        with open(self._updates_path, "w") as f:
            json.dump(self._updates, f)

    def _clean_record(self):
        to_delete = []
        for i, entry in enumerate(self._updates):
            _id = entry["id"]
            entry_time = float(_id.split("-")[-1])
            current_time = dt.utcnow().timestamp()

            if (current_time - entry_time) > self.save_time:
                to_delete.append(i)

        for i in sorted(to_delete, reverse=True):
            del self._updates[i]

    def _load_record(self):
        try:
            with open(self._updates_path, "r") as f:
                self._updates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self._updates_path, "w") as f:
                json.dump([], f)

# ------------------------------ END OF FILE ------------------------------
