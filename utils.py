import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from tqdm import tqdm

from DB import DB
import itertools

import platform

# curr_platform = "Win" if platform.platform().startswith("Windows") else "Mac" if platform.platform().startswith(
#     "macOS") else "Linux"
# if curr_platform == "Win":
#     DRIVER_LOCATION = "geckodriver.exe"
# elif curr_platform == "Mac":
#     DRIVER_LOCATION = "geckodriver"
# else:
#     print("Unknown platform")
# TESS_LOCATION =

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


def sleep(ts):
    # ts = 5
    for _ in tqdm(list(range(ts)), desc="Waiting...", position=0, leave=True):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Oh! You have sent a Keyboard Interrupt to me.\nBye, Bye")
            break


def generate_job_comb(dates):
    year_room_comb = list(itertools.product(*[dates, room_ranges, year_ranges]))
    return year_room_comb


def get_saved_files(verbose=False):
    path = "job_res"
    dirs = os.listdir(path)
    all_csv = []
    for d in sorted(dirs):
        all_csv += os.listdir(os.path.join(path, d))
        if verbose:
            print(d, len(os.listdir(os.path.join(path, d))))
        # # TODO: jsut do it again tommorow....
        # for f in os.listdir(os.path.join(path, d)):
        #     if d not in f:
        #         dt_heb = f[:10]
        #         suffix = f[10:]
        #         new_f = d + suffix
        #         print('old', f)
        #         print('new', new_f)
        #         try:
        #             os.rename(os.path.join(path, d, f), os.path.join(path, d, new_f))
        #         except Exception as e:
        #             print("Already exists")

    return all_csv


import requests

PROXY_API_KEY = "vsij00e8k9kh3nmrvss6"


def clear_and_add_my_ip():
    my_ip = requests.get("https://api.ipify.org?format=json").json()['ip']
    auth_ip = requests.get(
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_API_KEY}&type=get")
    # requests.get(f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={key}&type=remove&ip[]=1.1.1.1")
    whitelisted_ips = auth_ip.json()['whitelisted']
    if my_ip not in whitelisted_ips:
        if len(whitelisted_ips) == 3:
            res_remove_ip = requests.get(
                f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_API_KEY}&type=remove&ip[]={whitelisted_ips[0]}")
            if res_remove_ip.status_code == 200:
                print("removed an ip from proxy")
        res_add_ip = requests.get(
            f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_API_KEY}&type=add&ip[]=my_ip:{my_ip}")
        if res_add_ip.status_code == 200:
            print("Added IP to whitelist, now sleeping for 10MIN to allow smooth transit of proxies.")
            sleep(60 * 10)
        else:
            print("There was a problem...")
    else:
        print("IP already in system.")


def get_proxies():
    res = requests.get(
        f'https://api.proxyscrape.com/v2/account/datacenter_shared/proxy-list?auth={PROXY_API_KEY}&type=getproxies&country[]=all&protocol=http&format=normal&status=all')
    return [x.decode("utf-8") for x in res.content.splitlines()]


def format_job_to_file_csv(job):
    return f"{job[0].strftime('%Y-%m-%d')}_1_999999_{job[1][0]}_{job[1][1]}_{job[2][0]}_{job[2][1]}.csv"


def get_missing_combinations(all_dates):
    all_csv = get_saved_files()

    jobs_list = generate_job_comb(all_dates)
    job_list_str = [format_job_to_file_csv(x) for x in jobs_list]

    missing_jobs_packed = [(job, job_str) for job, job_str in zip(jobs_list, job_list_str) if job_str not in all_csv]
    missing_jobs, missing_jobs_str = list(zip(*missing_jobs_packed))
    with open("missing_jobs_str.txt", "w") as f:
        f.write('\n'.join(missing_jobs_str))
    return missing_jobs


def copy_csv_files_to_db(like=None):
    import os
    path = "job_res"
    import glob
    all_files = list(glob.iglob(path + '**/**', recursive=True))
    all_files = [f for f in all_files if f.endswith('.csv') and not f.startswith(".")]
    if like:
        print(f'Filtering by "{like}"')
        all_files = [f for f in all_files if like in f]
    with ThreadPoolExecutor(os.cpu_count()) as executor:
        futures = [executor.submit(lambda x: pd.read_csv(x), p) for p in all_files]
        dfs = [f.result() for f in futures]
    df = pd.concat(dfs, axis=0)
    from datetime import datetime
    df['insertionDate'] = df['insertionDate'].fillna(datetime.today())
    db = DB()
    db.insert_ignore(df)


def test_missing_combinations():
    all_dates = pd.date_range('2022-02-04', '2022-11-21')  # TODO: next to fill
    get_missing_combinations(all_dates)


def test_num_downloaded_files():
    get_saved_files(True)


def run_every_time_check_ip():
    while True:
        try:
            clear_and_add_my_ip()
        except Exception as e:
            pass
        time.sleep(15 * 60)


if __name__ == '__main__':
    pass
    # run_every_time_check_ip() -- added to scraper logic.
    # clear_and_add_my_ip()
    # test_num_downloaded_files()
    copy_csv_files_to_db()  # '2018'
    # test_missing_combinations()

# cear_and_add_my_ip()
# get_proxies()
# print(len(all_csv))
# copy_csv_files_to_db()
