import requests
import tenacity

from scrape_nadlan_gov.fetch import headers

url_cords = "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery"

from pyproj import Transformer


def itm_to_lat_long(x, y):
    # Israeli Transverse Mercator (ITM) projection
    # Convert ITM coordinates to WGS84 (latitude and longitude)
    transformer = Transformer.from_crs("epsg:2039", "epsg:4326")
    lat, long = transformer.transform(x, y)
    return lat, long


@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=3),
    stop=tenacity.stop_after_attempt(5),
    reraise=False
)
def get_nadlan_gov_cords(address_full):
    res = requests.get(url_cords, headers=headers, params={'query': address_full})
    # raise ValueError()
    res.raise_for_status()
    d = res.json()
    if d['ResultType'] == 0:
        print(f"GOV - Failed to get cords for address: {address_full}")
        return None
    lat, long = itm_to_lat_long(d['X'], d['Y'])
    return dict(lat=lat, long=long)


def _test():
    query1 = "ירושלים 22, ראשון לציון"
    query2 = "עפרה חזה 10 קרית מוצקין"  # failed
    query3 = "פתח תקווה יצחק שיפר 17"

    qs = [query1, query2, query3]

    for q in qs:
        try:
            res = get_nadlan_gov_cords(q)
            if res is not None:
                lat = res['lat']
                long = res['long']
                print(f"{q} ->\n {lat}, {long}")
        except tenacity.RetryError:
            print(f"Retries exhausted, function still failed. for query: {q}")

#
# {'ResultLable': 'לא קיים בנתונים', 'ResultType': 0, 'ObjectID': None, 'ObjectIDType': None, 'ObjectKey': None,
#  'DescLayerID': None, 'Alert': None, 'X': 0.0, 'Y': 0.0, 'Gush': None, 'Parcel': None, 'showLotParcel': False,
#  'showLotAddress': False, 'OriginalSearchString': None, 'MutipuleResults': False, 'ResultsOptions': None,
#  'CurrentLavel': 0, 'Navs': None, 'QueryMapParams': None, 'isHistorical': False, 'PageNo': 0, 'GridDisplayType': 0,
#  'FillterRoomNum': 0, 'MoreAssestsType': 0, 'OrderByFilled': 'DEALDATETIME', 'OrderByDescending': True, 'Distance': 0}
# {'ResultLable': 'שיפר יצחק 17, פתח תקוה', 'ResultType': 1, 'ObjectID': '53711025', 'ObjectIDType': 'text',
#  'ObjectKey': 'UNIQ_ID', 'DescLayerID': 'ADDR_V1', 'Alert': None, 'X': 189779.72842654, 'Y': 667100.2383939, 'Gush': '',
#  'Parcel': '', 'showLotParcel': False, 'showLotAddress': False, 'OriginalSearchString': 'פתח תקווה יצחק שיפר 17',
#  'MutipuleResults': False, 'ResultsOptions': None, 'CurrentLavel': 7,
#  'Navs': [{'text': 'פתח תקווה', 'url': 'פתח תקווה', 'order': 2},
#           {'text': 'שכונת שיפר', 'url': 'שכונת שיפר בפתח תקווה', 'order': 3},
#           {'text': 'יצחק שיפר', 'url': 'רחוב יצחק שיפר פתח תקווה', 'order': 4}],
#  'QueryMapParams': {'QueryToRun': None, 'QueryObjectID': '52322439', 'QueryObjectType': 'string',
#                     'QueryObjectKey': 'POLYGON_ID', 'QueryDescLayerID': 'KSHTANN_ASSETS', 'SpacialWhereClause': None},
#  'isHistorical': False, 'PageNo': 0, 'GridDisplayType': 0, 'FillterRoomNum': 0, 'MoreAssestsType': 0,
#  'OrderByFilled': 'DEALDATETIME', 'OrderByDescending': True, 'Distance': 0}
