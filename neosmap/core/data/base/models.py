import numpy as np
from config import MONITOR_TIME_INTERVAL, MPC_NEO_KEY_MAP
from neosmap.core.caching import APICache
from neosmap.logger import logger
import pandas as pd
import json


###########################################################################
# DEFINE BASE CLASS FOR NEO MONITOR

class NEOMonitorBase:

    def load_record(self):
        logger.debug("Loading NEO Monitor record")
        try:
            with open(self._updates_path, "r") as f:
                self._updates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self._updates_path, "w") as f:
                json.dump([], f)

    def _load_last_df(self):
        cache_ = APICache.get_instance("monitor")
        data = cache_.load(ignore_cache_valid=True)

        data_table = []
        for entry in data:
            parsed_entry = self._entry_parser(entry)
            data_table.append(parsed_entry)

        return pd.DataFrame(np.array(data), columns=MPC_NEO_KEY_MAP.values())

    @staticmethod
    def _entry_parser(entry):
        if not isinstance(entry, dict):
            return None

        parsed = []
        keys = [key for key in MPC_NEO_KEY_MAP.keys() if key != "vis"]
        for key in keys:
            parsed.append(entry[key])

        return parsed

# ------------------------------ END OF FILE ------------------------------
