from scrape_yad2.scraper_yad2 import ScraperYad2
from scrape_yad2.config import *
from sqlalchemy import create_engine
# from os import getcwd


def get_local_engine():
    eng = create_engine(f'sqlite:///../resources/yad2_test.db' )
    return eng


def get_scraper_yad2_forsale():
    scraper = ScraperYad2(url_forsale_apartments_houses, forsale_today_cols,
                          "yad2_forsale_today",
                          "yad2_forsale_history",
                          'yad2_forsale_log',
                          "yad2_forsale_items_add")
    return scraper


def get_scraper_yad2_rent():
    scraper = ScraperYad2(url_rent_apartments_houses, rent_today_cols,
                          "yad2_rent_today",
                          "yad2_rent_history",
                          'yad2_rent_log',
                          "yad2_rent_items_add")
    return scraper
