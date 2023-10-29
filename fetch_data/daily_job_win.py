# Workaround for python in windows...
from os.path import dirname
import sys

file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)

from stats.daily_fetch_nadlan_stats import run_nadlan_stats
from stats.daily_fetch_stats import run_type_stats

from fetch_data.daily_fetch_forsale import daily_forsale
from fetch_data.daily_fetch_rent import daily_rent
from fetch_data.daily.neighbors.calc import run_neighbors
from fetch_data.daily.find_assets.publish_ai_assets import find_and_publish_run_all
from scrape_nadlan.utils_insert import send_telegram_msg

if __name__ == '__main__':
    job_name = "DailyJob-Sale&Rent fetch and Calc"
    send_telegram_msg(f"⚪ Starting {job_name}")
    try:
        run_nadlan_stats()
        run_type_stats('forsale')
        run_type_stats('rent')
        daily_forsale()
        daily_rent()
        run_neighbors()
        find_and_publish_run_all()
        send_telegram_msg(f"🟢 FINISHED JOB in {job_name}")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))
        raise e
