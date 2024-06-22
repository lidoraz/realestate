import json

import requests
from typing import Optional, Dict
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPEN_STREET_MAP_URL = "https://nominatim.openstreetmap.org/search.php"


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    reraise=True
)
def fetch_data_from_osm(address_full: str) -> Optional[Dict[str, str]]:
    response = requests.get(
        OPEN_STREET_MAP_URL,
        headers={"User-Agent": "my-app"},
        params={"q": address_full, "format": "jsonv2"}
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        logger.info(f"No data found for address: {address_full}")
        return None
    return {"lat": data[0]["lat"], "long": data[0]["lon"]}


def get_lat_long_osm(address_full: str) -> Optional[Dict[str, str]]:
    if address_full is None:
        return None
    try:
        return fetch_data_from_osm(address_full)
    except (requests.RequestException, IndexError, KeyError, ValueError) as e:
        logger.error(f"Error fetching or processing data: {e}")
        return None


def add_lat_long_to_df(df, column_name="address"):
    lat_long = df[column_name].apply(get_lat_long_osm)
    lat_long = lat_long.apply(pd.Series)
    df = pd.concat([df, lat_long], axis=1)
    return df


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)
