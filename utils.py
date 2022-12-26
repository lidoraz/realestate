import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from DB import DB


def calc_missing_files():
    path = "job_res"
    dirs = os.listdir(path)
    for d in sorted(dirs):
        print(d, len(os.listdir(os.path.join(path, d))))


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

calc_missing_files()
# copy_csv_files_to_db()
