import logging
import os
from queue import Queue
import itertools
import random
import pandas as pd
from datetime import datetime, timedelta
from proxy.scrapeproxies import find_location
from scraper_logic import Scraper
from utils import get_missing_combinations, generate_job_comb

TIMEOUT_SEC = 120


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
            if proxy is not None:
                scraper.change_proxy(proxy)
            # scraper.driver.get("https://mylocation.org/")
            # res = {'status_code': 0}
            print(f"Started job: {params}, {proxy}, location = {find_location(proxy)}, {task_queue.qsize()}")
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


def run_multiple(jobs_list):
    task_queue.queue.clear()
    print(f" THERE ARE {len(jobs_list)} combinations!")
    tasks_params = [["1", "999999", *x] for x in jobs_list]
    # random.shuffle(tasks_params)
    for item in tasks_params:
        task_queue.put(item)
    # Block until all tasks are done.
    task_queue.join()
    print('All work completed')


def load_proxies(no_proxy=False):
    with open('proxyscrape_premium_http_proxies.txt', 'r') as f:
        proxies = f.read().splitlines()
        random.shuffle(proxies)
        for proxy in proxies:
            if no_proxy:
                proxy = None
                # proxy = "134.238.252.143:8080"
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


def run_logic():
    # import time
    # print("Sleeping...")
    # time.sleep(60 * 60 * 5)
    days_before = 35
      # 16

    # nice when no proxy works, it goes to sleep for 10 min automatically because of code.
    no_proxy = False
    if no_proxy:
        n_workers = 1
    else:
        n_workers = 12
        n_workers = 1
    load_proxies(no_proxy=no_proxy)
    start_threads(n_workers)

    all_dates = pd.date_range('2022-10-16', '2022-11-30')  # TODO: next to fill
    # all_dates = pd.date_range('2022-06-23', datetime.today() - timedelta(days=days_before))
    all_dates_str = [d for d in all_dates]
    jobs_list = get_missing_combinations(all_dates)
    # jobs_list = generate_job_comb(all_dates)
    run_multiple(jobs_list)
    close_scrapers()


if __name__ == '__main__':
    run_logic()
