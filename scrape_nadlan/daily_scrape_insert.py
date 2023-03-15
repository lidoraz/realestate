# Workaround for python in windows...
from os.path import dirname
import sys

file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)
from scrape_nadlan.insert_to_remote import insert_to_postgres_db
from scrape_nadlan.utils_insert import get_args, send_telegram_msg
from scrape_nadlan.Scraper.job import run_custom_job
from scrape_nadlan.Scraper.utils import copy_csv_files_to_db
import pandas as pd


def run_job(dt):
    run_custom_job(pd.date_range(dt, dt), filter_exists=False)
    copy_csv_files_to_db(dt)  # INSERTS TO SQLLITE DB!!!@@


if __name__ == '__main__':
    _dt = get_args()
    job_name = f"Scrape NADLAN with {_dt}"
    send_telegram_msg(f"⚪ Starting {job_name}")
    try:
        run_job(_dt)
        n_fetched, n_put = insert_to_postgres_db(_dt)
        if n_fetched == -1:
            raise Exception(f"no new data found for {_dt}")
        send_telegram_msg(f"🟢 FINISHED JOB in {job_name}, {_dt} ({n_fetched}, {n_put})")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))
