"""
Provides project wide configuration data. Includes filesystem locations, project information and constants.

Provides means to modify the configuration file using key value pairs from an interface.
"""

import os
import json
import logging

###########################################################################
# PROJECT FILESYSTEM DATA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CACHE_DIR = os.path.join(BASE_DIR, "cache")

CACHE_OBJECT_DIR = os.path.join(CACHE_DIR, "objects")
CACHE_LOG_DIR = os.path.join(CACHE_DIR, "log")
CACHE_TEMP_DIR = os.path.join(CACHE_DIR, "temp")
CACHE_DATA_DIR = os.path.join(CACHE_DIR, "data")

CONF_DIR = os.path.join(BASE_DIR, "conf")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# LOG FILE

if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "neosmap.log")
logging.basicConfig(
    filename=LOG_FILE,
    format='[%(asctime)s]: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    encoding='utf-8',
    level=logging.DEBUG
)

# SUB DIRECTORY STRUCTURES

TEMP_SUBDIRS = {
    "plot": os.path.join(CACHE_TEMP_DIR, "plot"),
    "script": os.path.join(CACHE_TEMP_DIR, "script"),
    "export": os.path.join(CACHE_TEMP_DIR, "export")
}

DATA_SUBDIRS = {
    "ephemerides": os.path.join(CACHE_DATA_DIR, "ephemerides"),
    "neocp": os.path.join(CACHE_DATA_DIR, "neocp"),
    "monitor": os.path.join(CACHE_DATA_DIR, "monitor")
}

LOG_SUBDIRS = {
    "ephemerides": os.path.join(CACHE_LOG_DIR, "ephemerides"),
    "neocp": os.path.join(CACHE_LOG_DIR, "neocp"),
    "monitor": os.path.join(CACHE_LOG_DIR, "monitor")
}

###########################################################################
# LOAD CONFIGURATION FILE

with open(os.path.join(CONF_DIR, "conf.json"), "r") as f:
    CONF = json.load(f)

###########################################################################
# PLOTTING

MONITOR_TIME_INTERVAL = CONF["monitor"]["interval"]

###########################################################################
# PLOTTING

TIME_INCR = CONF["visualization"]["plot"]["time_increments"]
OBS_TIME = CONF["visualization"]["plot"]["observation_time"]

###########################################################################
# DATA COLUMNS

COLUMNS = CONF["jpl"]["neo_list_keys"]
EXTENDED_COLS = CONF["jpl"]["neo_list_extended_keys"]
FILTERABLE_COLS = CONF["jpl"]["neo_list_numerically_filterable_keys"]
SCORE_COLUMNS = CONF["jpl"]["neo_list_scores"]
OVERVIEW_TABLE_COLS = CONF["jpl"]["neo_list_overview_table"]
MAIN_DISPLAYED_COLS = CONF["jpl"]["neo_list_keys_display"]
MPC_NEO_KEY_MAP = CONF["minor_planets_center"]["neo_list_keys_map"]

###########################################################################
# JPL SCOUT API

JPL_API_URL = CONF["jpl"]["scout_api"]["url"]
EPH_TIME_INCR = CONF["jpl"]["scout_api"]["eph_time_increment"]


###########################################################################
# MPC DATA

MPC_NEOCP_URL = CONF["minor_planets_center"]["neocp_url"]


###########################################################################
# CONFIGURATION FILE EDITOR

def edit_conf(key, value):

    with open(os.path.join(CACHE_DATA_DIR, "conf.json"), "r") as file:
        data = json.load(file)

    def _constraint(target):
        minimum, maximum = [CONF["constraints"][f"{qualifier}_{target}"] for qualifier in ["min", "max"]]
        return [minimum, maximum]

    if key in ["observation_time", "time_increments"]:
        if _constraint(key)[0] <= int(value) <= _constraint(key)[1]:
            data["visualization"]["plot"][key] = int(value)
        else:
            return False

    elif key in ["minimum_altitude"]:
        if _constraint(key)[0] <= int(value) <= _constraint(key)[1]:
            data["properties"]["observatory"][key] = int(value)
        else:
            return False

    else:
        return False

    with open(os.path.join(CACHE_DATA_DIR, "conf.json"), "w+") as file:
        json.dump(data, file, indent=2)

    return True

# ------------------------------ END OF FILE ------------------------------
