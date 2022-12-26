import logging
import os
from queue import Queue
import itertools
import random
import pandas as pd
from datetime import datetime, timedelta
from proxy.scrapeproxies import find_location
from scraper_logic import Scraper

TIMEOUT_SEC = 120
room_ranges = [
    ["1", "3.5"],
    # ["3", "3.5"],
    ["4", "4.5"],
    ["5", ""],
    # ["6", ""]
]
# year_ranges = [
#     ["1800", "1970"],
#     ["1971", "1980"],
#     ["1981", "1990"],
#     ["1991", "2000"],
#     ["2001", "2010"],
#     ["2011", "2100"]]
year_ranges = [
    ["1800", "1960"],
    ["1961", "1970"],
    ["1971", "1980"],
    ["1981", "1985"],
    ["1986", "1990"],
    ["1991", "1995"],
    ["1996", "2000"],
    ["2001", "2005"],
    ["2006", "2010"],
    ["2011", "2015"],
    ["2016", "2018"],
    ["2019", "2020"],
    ["2021", "2021"],
    ["2022", "2022"],
    ["2023", "2100"],
    # ["2023", "2023"],
    # ["2024", "2100"]
]


def get_daily_filtered_rooms_years(scraper, from_gush, to_gush, date, room_range, year_range):
    date_en = date.strftime('%Y-%m-%d')
    date_heb = date.strftime('%d/%m/%Y')
    file_name = f"{date_en}_{from_gush}_{to_gush}_{room_range[0]}_{room_range[1]}_{year_range[0]}_{year_range[1]}"
    try:
        scraper.get_page(timeout=TIMEOUT_SEC)
        scraper._from_gush = from_gush
        scraper._to_gush = to_gush
        scraper._date = date_heb
        scraper._from_room = room_range[0]
        scraper._to_room = room_range[1]
        scraper._from_year = year_range[0]
        scraper._to_year = year_range[1]
        logging.info(
            f"Fetching data for ({from_gush}, {to_gush}, {date_en}), for rooms in range {room_range}, year {year_range}")

        df, status_code = scraper.solve_captcha_get_data()
        if status_code == 0 or status_code == -1:
            if status_code == -1:
                logging.warning(f'{file_name} no deals found')
            dir_path = f"job_res/{date_en}"
            os.makedirs(dir_path, exist_ok=True)
            df.to_csv(os.path.join(dir_path, f'{file_name}.csv'), index=False)
        elif status_code == -2:
            with open("failed_due_to_too_many_deals.txt", 'a') as f:
                f.write(f'{file_name}\n')
            logging.critical(f"{file_name} FAILED TO GET EVEN WITH YEAR BUILT, RE THINK HOW TO SOLVE THIS MADDNESS")
    except Exception as e:
        logging.error(f'{file_name} FAILED !!!')
        logging.error(e)

        status_code = 1
    # import gc
    # gc.collect()
    return dict(file_name=file_name, status_code=status_code)

# PriorityQueue for not putting back tasks
# https://docs.python.org/3/library/queue.html


task_queue = Queue()
proxy_queue = Queue()
scrapers = []


def run():
    scraper = Scraper()
    scrapers.append(scraper)
    while True:
        proxy = proxy_queue.get()
        params = task_queue.get()
        try:
            scraper.change_proxy(proxy)
            # scraper.driver.get("https://mylocation.org/")
            # res = {'status_code': 0}
            print(f"Started job: {params}, {proxy}, location = {find_location(proxy)}")
            res = get_daily_filtered_rooms_years(scraper, *params)
            if res['status_code'] == 1:  # task failed
                task_queue.put(params)
            else:
                print(res, task_queue.qsize())
                # print(task_queue.qsize())

            # https://stackoverflow.com/questions/49637086/python-what-is-queue-task-done-used-for

        except Exception as e:
            print("Caught an exception", os.getpid(), e)
            task_queue.put(params)
        task_queue.task_done()
        proxy_queue.put(proxy)

def run_multiple(dates):
    task_queue.queue.clear()
    year_room_comb = list(itertools.product(*[dates, room_ranges, year_ranges]))

    print(f" THERE ARE {len(year_room_comb)} combinations!")
    tasks_params = [["1", "999999", *x] for x in year_room_comb]
    # random.shuffle(tasks_params)
    for item in tasks_params:
        task_queue.put(item)
    # Block until all tasks are done.
    task_queue.join()
    print('All work completed')


def load_proxies():
    with open('proxyscrape_premium_http_proxies.txt', 'r') as f:
        proxies = f.read().splitlines()
        random.shuffle(proxies)
        for proxy in proxies:
            # proxy = None # for disabling it
            proxy_queue.put(proxy)


def start_threads(n_workers):
    import threading
    threads = [threading.Thread(target=run, daemon=True) for _ in range(n_workers)]
    for t in threads:
        t.start()
    return threads


def close_scrapers():
    for scraper in scrapers:
        scraper.close()


if __name__ == '__main__':
    import time
    # print("Sleeping...")
    # time.sleep(60*3)
    print("Starting with new config, good luck...")
    days_before = 35
    n_workers = 12  # 16
    load_proxies()
    start_threads(n_workers)


    # all_dates = pd.date_range('2022-03-22', '2022-06-21')
    all_dates = pd.date_range('2022-06-23', datetime.today() - timedelta(days=days_before))
    all_dates_str = [d for d in all_dates]

    run_multiple(all_dates)
    close_scrapers()

