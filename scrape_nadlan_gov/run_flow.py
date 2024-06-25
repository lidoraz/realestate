import pandas as pd

from scrape_nadlan_gov.fetch import concurrent_fetch_all_cities
from scrape_nadlan_gov.insert import insert_new_rows, create_table
from scrape_nadlan_gov.process import process_nadlan_data
from scrape_nadlan_gov.update_cords import process_missing_coordinates

from ext.env import get_pg_engine


# def get_pg_engine():  ## TODO: VERY RISKY SHOULD BE HERE ONLY WHEN DONE
#     import os
#     from sqlalchemy import create_engine
#     # DATABASE_URI = os.getenv('DATABASE_URI')
#     DATABASE_URI = 'sqlite:///real_estate_deals.db'
#     return create_engine(DATABASE_URI)


def run_daily_flow():
    max_days_back = 30 * 4
    # max_days_back = 30
    engine = get_pg_engine()
    create_table(engine)
    # df = pd.read_pickle("run_flow_df_23_june.pickle")
    # df = pd.read_pickle("run_flow_df_24_june.pickle")
    df = concurrent_fetch_all_cities(max_days_back=max_days_back, max_workers=10)
    df = process_nadlan_data(df)
    print("Memory usage: ", df.memory_usage().sum() / 1e6, "MB")
    # df.to_pickle("run_flow_df_24_june.pickle")
    n_rows = insert_new_rows(df, engine, max_days_back)
    n_fixed_deals = process_missing_coordinates(engine)
    print("Inserted ", n_rows, " new rows", n_fixed_deals, "fixed deals")


if __name__ == '__main__':
    run_daily_flow()
