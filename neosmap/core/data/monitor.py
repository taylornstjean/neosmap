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
    """Stores an access pointer to monitoring data for each user. Data is routinely updated by a backend process."""

    def __init__(self, *args, **kwargs):
        super(NEOMonitor, self).__init__(*args, **kwargs)

        self._ignore_id_path = os.path.join(CACHE_USER_DIR, "{}_ignore_ids.json".format(current_user.id))

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

    def __init__(self, app, *args, **kwargs):
        super(NEOMonitorDaemon, self).__init__(*args, **kwargs)

        self._app = app


# ------------------------------ END OF FILE ------------------------------
