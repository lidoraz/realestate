# Workaround for python in windows...
import os
from ext.env import load_vault

load_vault()  # load env to prod
from os.path import dirname
import sys

file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)

from stats.daily_fetch_nadlan_stats import run_nadlan_stats
from fetch_data.daily_fetch_forsale import daily_forsale
from fetch_data.daily_fetch_rent import daily_rent
from fetch_data.neighbors.calc import run_neighbors
from fetch_data.find_assets.publish_ai_assets import find_and_publish_run_all
from fetch_data.find_assets.publish_ai_assets_all import find_and_publish_for_all_users
from scrape_nadlan.utils_insert import send_telegram_msg

import time

# from stats.daily_fetch_stats import run_type_stats

if __name__ == '__main__':
    job_name = "DailyJob-Sale&Rent Preprocess"
    send_telegram_msg(f"⚪ Starting {job_name}")
    model_params = dict(n_folds=5, iterations=5000)
    try:
        run_nadlan_stats()  ## Needed until main plot will be via api
        daily_forsale(model_params=model_params)
        daily_rent(model_params=model_params)
        run_neighbors()
        find_and_publish_run_all()  # for me
        # this code goes out to other process..
        # time.sleep(60 * 5)  # sleep for 5 minutes to allow site to update...
        # find_and_publish_for_all_users() # for all others
        send_telegram_msg(f"🟢 FINISHED JOB in {job_name}")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))
        raise e
