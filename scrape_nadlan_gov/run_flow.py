from scrape_nadlan_gov.fetch import concurrent_fetch_all_cities
from scrape_nadlan_gov.insert import insert_new_rows, create_table
from scrape_nadlan_gov.process import process_nadlan_data
from scrape_nadlan_gov.update_cords import process_missing_coordinates
from ext.env import get_pg_engine
import os
from datetime import datetime


def run_daily_flow():
    max_days_back = int(os.environ.get("MAX_DAYS_BACK", 30 * 4))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(now, "Running daily flow with max_days_back=", max_days_back)

    engine = get_pg_engine()
    create_table(engine)
    df = concurrent_fetch_all_cities(max_days_back=max_days_back, max_workers=10)
    df = process_nadlan_data(df)
    n_rows = insert_new_rows(df, engine, max_days_back)
    n_fixed_deals = process_missing_coordinates(engine)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(now,
          "Inserted ",
          n_rows,
          " new rows",
          n_fixed_deals,
          "fixed deals")


if __name__ == '__main__':
    run_daily_flow()
