# Workaround for python in windows...
from os.path import dirname
import sys
file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)


from NadlanScraper.utils_insert import get_args
from NadlanScraper.Scraper.job import run_custom_job
from NadlanScraper.Scraper.utils import copy_csv_files_to_db
import pandas as pd


def run_job(dt):
    run_custom_job(pd.date_range(dt, dt), filter_exists=False)
    copy_csv_files_to_db(dt)


if __name__ == '__main__':
    _dt = get_args()
    print(f"Scrape started with {_dt}")
    run_job(_dt)
