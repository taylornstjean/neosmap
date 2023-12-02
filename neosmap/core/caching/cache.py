"""
Provides means to log data modifications and updates.
"""

import os
import pickle
import json
from config import LOG_SUBDIRS, CACHE_DIR
from .exceptions import CacheTimeExceededError

from datetime import datetime as dt
import logging

eph_log_dir = LOG_SUBDIRS["ephemerides"]


class APICache:

    instances = {}
    object_dir = os.path.join(CACHE_DIR, "objects")

    def __init__(self, name, cache_type, cache_time):
        self.name = name
        self._cache_type = cache_type
        self._pkl_path = os.path.join(self.object_dir, f"{name}.pkl")
        self._cache_time = cache_time
        self.instances[name] = self

    def _file_path(self, dir_, file_type):
        path = os.path.join(CACHE_DIR, dir_, self._cache_type, f"{self.name}.{file_type}")
        return path

    def _pickle_save(self):
        with open(self._pkl_path, "wb") as f:
            pickle.dump(self, f)

    def save(self, data):
        with open(self._file_path("data", "json"), "w") as f:
            json.dump(data, f)

        with open(self._file_path("log", "log"), "w") as f:
            time_ = str(dt.utcnow().timestamp())
            f.write(time_)

        self._pickle_save()

    def load(self, ignore_cache_valid=False):
        if not self.valid and not ignore_cache_valid:
            raise CacheTimeExceededError(self.name)

        with open(self._file_path("data", "json"), "r") as f:
            data = json.load(f)

        return data

    @property
    def valid(self):
        with open(self._file_path("log", "log"), "r") as f:
            time_log = float(f.read())

        time_now = dt.utcnow().timestamp()

        if (time_now - time_log) >= self._cache_time:
            return False

        return True

    @property
    def verify(self):
        data_file = os.path.isfile(self._file_path("data", "json"))
        log_file = os.path.isfile(self._file_path("log", "log"))

        return all([data_file, log_file])

    @property
    def age(self):
        with open(self._file_path("log", "log"), "r") as f:
            time_log = float(f.read())

        time_now = dt.utcnow().timestamp()

        return time_now - time_log

    def delete(self):
        data_file = self._file_path("data", "json")
        log_file = self._file_path("log", "log")
        pkl_file = self._pkl_path

        for file in [data_file, log_file, pkl_file]:
            try:
                os.remove(file)

            except FileNotFoundError:
                pass

        del self.instances[self.name]

    @classmethod
    def get_instance(cls, name):
        try:
            return cls.instances[name]

        except KeyError:
            raise ValueError("No instance exists with name \'{}\'.".format(name))

    @classmethod
    def clean(cls):
        to_delete = []
        for name, instance in cls.instances.items():
            if not instance.valid or not instance.verify:
                to_delete.append(instance)
        for instance in to_delete:
            instance.delete()

    @classmethod
    def load_instances(cls):
        try:
            for file in os.listdir(cls.object_dir):
                file_path = os.path.join(cls.object_dir, file)
                with open(file_path, "rb") as f:
                    try:
                        instance = pickle.load(f)
                        cls.instances[instance.name] = instance

                    except EOFError:
                        pass

        except FileNotFoundError:
            pass


###########################################################################
# INTERNAL FUNCTIONS


def _get_last_line(file_stream):
    try:  # catch OSError in case of a one line file
        file_stream.seek(-2, os.SEEK_END)
        while file_stream.read(1) != b'\n':
            file_stream.seek(-2, os.SEEK_CUR)
    except OSError:
        file_stream.seek(0)
    try:
        return float(file_stream.readline().decode())
    except ValueError:
        return None


###########################################################################
# EPHEMERIS DATA LOGGER

def ephemeris_last_cache(tdes: str):
    """
    Check when last ephemeris api pull occurred. If no data saved, returns None.

    :param tdes: Specify NEO temporary designation to check its last ephemeris data save.
    :type tdes: str
    """

    try:
        with open(os.path.join(eph_log_dir, f"{tdes}.log"), "rb") as f:
            return _get_last_line(f)
    except FileNotFoundError:
        with open(os.path.join(eph_log_dir, f"{tdes}.log"), "w") as _:
            pass
        return None


def ephemeris_log_cache(tdes: str) -> None:
    """
    Log ephemeris api pull.

    :param tdes: Specify NEO temporary designation for which a data pull has occurred.
    :type tdes: str
    """

    with open(os.path.join(eph_log_dir, f"{tdes}.log"), "a") as f:
        entry = f"{dt.utcnow().timestamp()}\n"
        f.write(entry)


###########################################################################
# LOG DIRECTORY CLEANUP

def clean_ephemeris_cache(neo_data):
    """
    Clean ephemeris pull logs. Removes associated log file if its object was removed from the MPC/JPL database.

    :param neo_data: NEOData object.
    :type neo_data: NEOData
    """
    df = neo_data.df()
    logging.debug(f"Cleaning ephemeris cache.")
    for file in os.listdir(eph_log_dir):
        tdes = file.split(".")[0]
        if not (df['objectName'].eq(tdes)).any():
            os.remove(os.path.join(eph_log_dir, file))

# ------------------------------ END OF FILE ------------------------------
