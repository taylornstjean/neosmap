"""
Provides means to log data modifications and updates.
"""

import os
from config import LOG_SUBDIRS
from datetime import datetime as dt

neocp_log_path = os.path.join(LOG_SUBDIRS["neocp"], "neocp.log")
eph_log_dir = LOG_SUBDIRS["ephemerides"]


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
# NEOCP FILE LOGGER

def neocp_last_save():
    """Check when last neocp file pull occurred. If no data saved, returns None."""

    try:
        with open(neocp_log_path, "rb") as f:
            return _get_last_line(f)
    except FileNotFoundError:
        with open(neocp_log_path, "w") as f:
            pass
        return None


def neocp_log_save():
    """Log neocp file pull."""

    with open(neocp_log_path, "a") as f:
        entry = f"{dt.utcnow().timestamp()}\n"
        f.write(entry)


###########################################################################
# EPHEMERIS DATA LOGGER

def ephemeris_last_save(tdes: str):
    """
    Check when last ephemeris api pull occurred. If no data saved, returns None.

    :param tdes: Specify NEO temporary designation to check its last ephemeris data save.
    :type tdes: str
    """

    try:
        with open(os.path.join(eph_log_dir, f"{tdes}.log"), "rb") as f:
            return _get_last_line(f)
    except FileNotFoundError:
        with open(os.path.join(eph_log_dir, f"{tdes}.log"), "w") as f:
            pass
        return None


def ephemeris_log_save(tdes: str) -> None:
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

def clean_logs(neo_data):
    """
    Clean ephemeris pull logs. Removes associated log file if its object was removed from the MPC/JPL database.

    :param neo_data: NEOData object.
    :type neo_data: NEOData
    """
    for file in os.listdir(eph_log_dir):
        tdes = file.split(".")[0]
        if not (neo_data.df()['objectName'].eq(tdes)).any():
            os.remove(os.path.join(eph_log_dir, file))

# ------------------------------ END OF FILE ------------------------------
