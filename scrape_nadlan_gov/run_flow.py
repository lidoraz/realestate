from scrape_nadlan_gov.fetch import concurrent_fetch_all_cities
from scrape_nadlan_gov.insert import insert_new_rows
from scrape_nadlan_gov.process import process_nadlan_data
from scrape_nadlan_gov.update_cords import process_missing_coordinates
from ext.env import get_pg_engine


def run_daily_flow():
    max_days_back = 30 * 4
    df = concurrent_fetch_all_cities(max_days_back=max_days_back, max_workers=10)
    df = process_nadlan_data(df)
    print("Memory usage: ", df.memory_usage().sum() / 1e6, "MB")

    engine = get_pg_engine()
    n_rows = insert_new_rows(df, engine)
    n_fixed_deals = process_missing_coordinates(engine)
    print("Inserted ", n_rows, " new rows", n_fixed_deals, "fixed deals")
