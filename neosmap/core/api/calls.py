from ratelimit import limits, sleep_and_retry
from urllib.request import urlopen
import json
from config import JPL_API_URL, MPC_NEOCP_URL


@sleep_and_retry
@limits(calls=1, period=10)
def retrieve_data_jpl():
    with urlopen(JPL_API_URL) as url:
        loaded_data = json.load(url)

    return loaded_data


@sleep_and_retry
@limits(calls=1, period=10)
def retrieve_data_jpl_ephemerides():
    with urlopen(JPL_API_URL) as url:
        loaded_data = json.load(url)

    return loaded_data


@sleep_and_retry
@limits(calls=1, period=40)
def retrieve_data_mpc():
    with urlopen(MPC_NEOCP_URL) as url:
        loaded_data = json.load(url)

    return loaded_data

# ------------------------------ END OF FILE ------------------------------
