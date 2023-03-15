import os
import time
import schedule
from datetime import datetime

from scrape_nadlan.utils_insert import get_engine, send_telegram_msg
from scrape_yad2.run import get_scraper_yad2_forsale, get_scraper_yad2_rent


def _scraper():
    engine = get_engine()
    with engine.connect() as conn:
        print(f"{datetime.today()} Starting to fetch!")
        scraper = get_scraper_yad2_forsale()
        scraper.scraper_yad2(conn)
        print(f"{datetime.today()} Finished get_scraper_yad2_forsale!")
        scraper = get_scraper_yad2_rent()
        scraper.scraper_yad2(conn)
        print(f"{datetime.today()} Finished!")
    engine.dispose()


def routine_daily_yad2_to_db():
    # time_fetch = "18:00"
    print("Fetching yad2 Started")
    # print(f"Will fetch every day at: {time_fetch} UTC")
    _scraper()
    # schedule.every().day.at(time_fetch).do(_scraper)  # should be 20:00 ISR time
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)


if __name__ == '__main__':
    job_name = f"YAD2 Crawler"
    send_telegram_msg(f"⚪ Starting {job_name}")
    try:
        routine_daily_yad2_to_db()
        send_telegram_msg(f"🟢 FINISHED JOB in {job_name}")
    except Exception as e:
        send_telegram_msg(f"🔴 ERROR in {job_name}")
        send_telegram_msg(str(e))


