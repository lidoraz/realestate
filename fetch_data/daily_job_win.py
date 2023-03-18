# Workaround for python in windows...
from os.path import dirname
import sys

file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)

from stats.daily_fetch_nadlan_stats import run_nadlan_stats
from stats.daily_fetch_stats import run_type_stats

from fetch_data.daily_fetch_forsale import daily_forsale
from fetch_data.daily_fetch_rent import daily_rent

from scrape_nadlan.utils_insert import send_telegram_msg

if __name__ == '__main__':
    job_name = "DailyJob-Sale&Rent fetch and Calc"
    send_telegram_msg(f"⚪ Starting {job_name}")
    try:
        run_type_stats('forsale')
        run_type_stats('rent')
        run_nadlan_stats()
        daily_forsale()
        daily_rent()
        send_telegram_msg(f"🟢 FINISHED JOB in {job_name}")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))
        raise e
