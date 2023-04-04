import logging
import os
from queue import Queue
import random
import pandas as pd
from datetime import datetime, timedelta
from scrape_nadlan.Scraper.logic import Scraper
from scrape_nadlan.Scraper.utils import get_missing_combinations, generate_job_comb, clear_and_add_my_ip, \
    run_every_time_check_ip, \
    copy_csv_files_to_db
import threading
import time
TIMEOUT_SEC = 120


def get_daily_filtered_rooms_years(scraper, from_gush, to_gush, date, room_range, year_range):
    date_en = date.strftime('%Y-%m-%d')
    date_heb = date.strftime('%d/%m/%Y')
    file_name = f"{date_en}_{from_gush}_{to_gush}_{room_range[0]}_{room_range[1]}_{year_range[0]}_{year_range[1]}"
    n_rows = -1
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
            n_rows = len(df)
        elif status_code == -2:
            with open("../../failed_due_to_too_many_deals.txt", 'a') as f:
                f.write(f'{file_name}\n')
            logging.critical(f"{file_name} FAILED TO GET EVEN WITH YEAR BUILT, RE THINK HOW TO SOLVE THIS MADDNESS")
    except Exception as e:
        logging.error(f'{file_name} FAILED !!!')
        logging.error(e)

        status_code = 1
    # import gc
    # gc.collect()
    return dict(file_name=file_name, status_code=status_code, n_rows=n_rows)


# PriorityQueue for not putting back tasks
# https://docs.python.org/3/library/queue.html


task_queue = Queue()
proxy_queue = Queue()
scrapers = []


def start_routine(use_proxy):
    scraper = Scraper(headless=True)
    scrapers.append(scraper)
    while True:
        proxy = None
        if use_proxy:
            proxy = proxy_queue.get()
        params = task_queue.get()
        try:
            if use_proxy and proxy is not None:
                scraper.change_proxy(proxy)
            # scraper.driver.get("https://www.iplocation.net/")
            # res = {'status_code': 0}
            print(f"Started job: {params}, {proxy}, {task_queue.qsize()}")
            # print(f"Started job: {params}, {proxy}, location = {find_location(proxy)}, {task_queue.qsize()}")
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
        if use_proxy:
            proxy_queue.put(proxy)
        time.sleep(5)


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
    with open('resources/proxyscrape_premium_http_proxies.txt', 'r') as f:
        proxies = f.read().splitlines()
        random.shuffle(proxies)
        for proxy in proxies:
            if no_proxy:
                proxy = None
                # proxy = "134.238.252.143:8080"
            # proxy = None # for disabling it
            proxy_queue.put(proxy)


def start_threads(n_workers, use_proxy):
    threads = [threading.Thread(target=start_routine, daemon=True, args=(use_proxy,)) for _ in range(n_workers)]
    for t in threads:
        t.start()
    return threads


def close_scrapers():
    for scraper in scrapers:
        scraper.close()


def run_daily_job():
    # ADD HERE DO EVERY ONE DAY BLAH BLAH....
    # This does not need any fancy proxies, as it will only use 1 thread to get all the data throughout the day
    days_before = 30
    curr_date = datetime.today() - timedelta(days=days_before)
    jobs_list = generate_job_comb(pd.date_range(curr_date, curr_date))
    load_proxies(no_proxy=True)
    start_threads(1, use_proxy=False)
    run_multiple(jobs_list)


def run_custom_job(date_range, filter_exists, use_proxy=False):
    # TODO: When blocked the block will be for 1 week, or atleast 5 days (wednsday to sunday)
    #  They block entire IP outside of Israel, not specific ones
    # nice when no proxy works, it goes to sleep for 10 min automatically because of code.
    no_proxy = False
    no_proxy = not use_proxy
    if no_proxy:
        print("not using proxy")
        n_workers = 1
    else:
        clear_and_add_my_ip()
        n_workers = 24
        threading.Thread(target=run_every_time_check_ip, daemon=True).start()
        load_proxies(no_proxy=no_proxy)
    start_threads(n_workers, use_proxy)

    if filter_exists:
        date_range = date_range.tolist()[::-1]  # Reverse them
        jobs_list = get_missing_combinations(date_range)
    else:
        jobs_list = generate_job_comb(date_range)
    # jobs_list = jobs_list[:1]
    run_multiple(jobs_list)
    close_scrapers()


def run_custom_job_history():
    date_range = pd.date_range('2017-01-01', '2017-12-31')
    run_custom_job(date_range, filter_exists=True)


def run_custom_job_recent():
    run_custom_job(pd.date_range('2022-12-01', '2022-12-31'), filter_exists=False)


def run_daily(days_back):
    def job():
        dt = str((datetime.today() - timedelta(days=days_back)).date())
        run_custom_job(pd.date_range(dt, dt), filter_exists=False)
        copy_csv_files_to_db(dt)

    job()
    # schedule.every(1).day.do(job)
    # schedule.every(1).day.at("00:00").do(job)
    # schedule.every(20).seconds.do(job)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)


if __name__ == '__main__':
    import time

    run_daily(45)
    # 2022-11-19
    # run_custom_job(pd.date_range('2022-11-20', '2023-01-20'), filter_exists=False)

    # print("Sleeping...")
    # time.sleep(60 * 5)
    # time.sleep(60 * 60 * 1)
    # run_custom_job_history()
    # run_custom_job_recent()
    # run_custom_job(pd.date_range('2022-12-15', '2023-01-15'), filter_exists=False)
