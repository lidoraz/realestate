import tenacity
from typing import Optional, Dict
import requests

OPEN_STREET_MAP_URL = "https://nominatim.openstreetmap.org/search.php"


@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(5),
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
        print(f"OSM - No data found for address: {address_full}")
        return None
    return {"lat": data[0]["lat"], "long": data[0]["lon"]}
