import numpy as np
from config import CACHE_USER_DIR
from flask_login import current_user
from .base import NEOMonitorBase
from datetime import datetime as dt
import pandas as pd
import os
import json
from neosmap.logger import logger


###########################################################################
# DEFINE NEO MONITOR AND NEO MONITOR DAEMON CLASS

class NEOMonitor(NEOMonitorBase):

    def __init__(self, *args, **kwargs):
        super(NEOMonitor, self).__init__(*args, **kwargs)

        self._ignore_id_path = os.path.join(CACHE_USER_DIR, "{}_ignore_ids.json".format(current_user.id))

    def get_ignore_ids(self, timestamp=False):
        try:
            with open(self._ignore_id_path, "r") as f:
                data = json.load(f)
                if not timestamp:
                    return [entry["id"] for entry in data]

                return data

        except FileNotFoundError:
            return []

        except json.JSONDecodeError:
            with open(self._ignore_id_path, "w") as f:
                json.dump([], f)
            return []

    def save_ignore_ids(self, ids):
        current_time = dt.utcnow().timestamp()
        data = self.get_ignore_ids(timestamp=True)

        for _id in ids:
            data.append({"id": _id, "ts": current_time})

        with open(self._ignore_id_path, "w") as f:
            json.dump(data, f, indent=4)

    def _clean_ignore_ids(self):
        data = self.get_ignore_ids(timestamp=True)
        to_delete = []
        current_time = dt.utcnow().timestamp()
        current_ids = [update["id"] for update in self._updates]

        for i, entry in enumerate(data):
            if (current_time - entry["ts"]) >= self.save_time:
                to_delete.append(i)
            elif entry["id"] not in current_ids:
                to_delete.append(i)

        for i in sorted(to_delete, reverse=True):
            del data[i]

        with open(self._ignore_id_path, "w") as f:
            json.dump(data, f, indent=4)

    def _remove_ignore_id(self, _id):
        data = self.get_ignore_ids(timestamp=True)
        filtered_data = [entry for entry in data if entry["id"] != _id]

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
        self.check_update()
        logger.debug("NEO Monitor data update complete")
        _data = {
            "df": self._load_last_df(),
            "updates": pd.DataFrame(self._updates)
        }
        return _data


class NEOMonitorDaemon(NEOMonitorBase):

    def __init__(self, *args, **kwargs):
        super(NEOMonitorDaemon, self).__init__(*args, **kwargs)


# ------------------------------ END OF FILE ------------------------------
