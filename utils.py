import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from DB import DB
import itertools

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


def generate_job_comb(dates):
    year_room_comb = list(itertools.product(*[dates, room_ranges, year_ranges]))
    return year_room_comb


def get_saved_files():
    path = "job_res"
    dirs = os.listdir(path)
    all_csv = []
    for d in sorted(dirs):
        all_csv += os.listdir(os.path.join(path, d))
        # print(d, len(os.listdir(os.path.join(path, d))))
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


def clear_and_add_my_ip():
    auth_ip = requests.get(
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_API_KEY}&type=get")
    # requests.get(f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={key}&type=remove&ip[]=1.1.1.1")
    ips = auth_ip.json()['whitelisted']
    if len(ips):
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_API_KEY}&type=remove&ip[]={ips[0]}"
    my_ip = requests.get("https://api.ipify.org?format=json").json()['ip']
    res = requests.get(
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_API_KEY}&type=add&ip[]=my_ip{my_ip}")
    return


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

    missing_jobs = [job for job, job_str in zip(jobs_list, job_list_str) if job_str not in all_csv]
    # for f in sorted(missing_jobs):
    #     print(f)
    return missing_jobs


def copy_csv_files_to_db():
    import os
    path = "job_res"
    import glob
    all_files = []
    for filename in glob.iglob(path + '**/**', recursive=True):
        if filename.endswith('.csv'):
            all_files.append(filename)

    with ThreadPoolExecutor(os.cpu_count()) as executor:
        futures = [executor.submit(lambda x: pd.read_csv(x), p) for p in all_files]
        dfs = [f.result() for f in futures]
    df = pd.concat(dfs, axis=0)
    from datetime import datetime
    df['insertionDate'] = df['insertionDate'].fillna(datetime.today())
    db = DB()
    db.insert_ignore(df)
    # files = os.listdir(path)

    # df = pd.DataFrame()
    # for file in files:
    #     df_s = pd.read_csv(os.path.join(path, file))
    #     df = pd.concat([df, df_s], axis=0)
    # from datetime import datetime
    # df['insertionDate'] = datetime.today()
    # db.insert_ignore(df)


def tests():
    all_csv = get_saved_files()

    all_dates = pd.date_range('2022-02-04', '2022-11-21')  # TODO: next to fill
    get_missing_combinations(all_dates)


if __name__ == '__main__':
    tests()

# clear_and_add_my_ip()
# get_proxies()
# all_csv = get_saved_files()
# print(len(all_csv))
# copy_csv_files_to_db()
