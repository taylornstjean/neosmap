from ratelimit import limits, sleep_and_retry
from urllib.request import urlopen
import logging
import json
from config import JPL_API_URL, MPC_NEOCP_URL


@sleep_and_retry
@limits(calls=1, period=10)
def retrieve_data_jpl():
    logging.warning(f"Pulling data from {JPL_API_URL}.")
    with urlopen(JPL_API_URL) as url:
        loaded_data = json.load(url)

    return loaded_data


@sleep_and_retry
@limits(calls=1, period=10)
def retrieve_data_jpl_ephemerides():
    logging.warning(f"Pulling data from {JPL_API_URL}.")
    with urlopen(JPL_API_URL) as url:
        loaded_data = json.load(url)

    return loaded_data


@sleep_and_retry
@limits(calls=1, period=40)
def retrieve_data_mpc():
    logging.warning(f"Pulling data from {MPC_NEOCP_URL}.")
    with urlopen(MPC_NEOCP_URL) as url:
        loaded_data = json.load(url)

    return loaded_data
