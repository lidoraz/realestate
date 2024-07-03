import os
os.chdir('..')

import json
import unittest
from unittest import mock

from scrape_nadlan_gov.process import process_nadlan_data
from scrape_nadlan_gov.update_cords import add_lat_long_to_df


def mock_make_request_ordered(payload):
    with open("tests/resources/response.json", "r") as f:
        data = json.load(f)
    return data, 200


class TestFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mock.patch("scrape_nadlan_gov.fetch_utils.make_request_ordered", mock_make_request_ordered).start()

    def test_fetch_by_city_id(self):
        from scrape_nadlan_gov.fetch import fetch_by_city

        df = fetch_by_city('בת ים', 10, max_pages=2)
        print(df)

    def test_fetch_by_city_id_preprocess_get_cords(self):
        from scrape_nadlan_gov.fetch import fetch_by_city
        import pandas as pd
        df = fetch_by_city('חיפה', 10, max_pages=2)
        df['city'] = 'test'
        df = process_nadlan_data(df)
        df = add_lat_long_to_df(df)
        print(df)


if __name__ == '__main__':
    unittest.main()
