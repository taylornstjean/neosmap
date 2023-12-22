"""
Provides project wide configuration data. Includes filesystem locations, project information and constants.

Provides means to modify the configuration file using key value pairs from an interface.
"""

import os
import json

###########################################################################
# PROJECT FILESYSTEM DATA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CACHE_DIR = os.path.join(BASE_DIR, "cache")

CACHE_OBJECT_DIR = os.path.join(CACHE_DIR, "objects")
CACHE_LOG_DIR = os.path.join(CACHE_DIR, "log")
CACHE_TEMP_DIR = os.path.join(CACHE_DIR, "temp")
CACHE_DATA_DIR = os.path.join(CACHE_DIR, "data")
CACHE_USER_DIR = os.path.join(CACHE_DIR, "user")

CONF_DIR = os.path.join(BASE_DIR, "conf")
LOG_DIR = os.path.join(BASE_DIR, "logs")

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

COLUMNS = list(CONF["jpl"]["neo_list_keys"].keys())
EXTENDED_COLS = {col: vals["ext"] for col, vals in CONF["jpl"]["neo_list_keys"].items()}
FILTERABLE_COLS = CONF["jpl"]["neo_list_numerically_filterable_keys"]
SCORE_COLUMNS = [col for col, vals in CONF["jpl"]["neo_list_keys"].items() if vals["is_score"]]
OVERVIEW_TABLE_COLS = CONF["jpl"]["neo_list_overview_table"]
MAIN_DISPLAYED_COLS = [col for col, vals in CONF["jpl"]["neo_list_keys"].items() if vals["display"]]
MPC_NEO_KEY_MAP = CONF["minor_planets_center"]["neo_list_keys_map"]

###########################################################################
# JPL SCOUT API

JPL_API_URL = CONF["jpl"]["scout_api"]["url"]
EPH_TIME_INCR = CONF["jpl"]["scout_api"]["eph_time_increment"]


###########################################################################
# MPC DATA

MPC_NEOCP_URL = CONF["minor_planets_center"]["neocp_url"]


# ------------------------------ END OF FILE ------------------------------
