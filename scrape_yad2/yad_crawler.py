"""
# Collect Tweets logic: Save in db by name and ts, if exists, ignore it, check every 30sec. limit is 900 per 15min
"""
import os
import time
import schedule
from datetime import datetime
from scrape_yad2.run import get_scraper_yad2_forsale, get_scraper_yad2_rent
from sqlalchemy import create_engine


def _scraper():
    engine = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@localhost:5432/vsdatabase')
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
    time_fetch = "18:00"
    print(f"Will fetch every day at: {time_fetch} UTC")
    # _scraper()
    schedule.every().day.at(time_fetch).do(_scraper)  # should be 20:00 ISR time
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    routine_daily_yad2_to_db()
