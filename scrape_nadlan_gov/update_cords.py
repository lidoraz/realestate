import requests
import tenacity
from sqlalchemy.orm import sessionmaker
from scrape_nadlan_gov.insert import NadlanGovTrans
from scrape_nadlan_gov.cords_gov import get_nadlan_gov_cords
from scrape_nadlan_gov.cords_osm import fetch_data_from_osm
from tqdm import tqdm
import pandas as pd
import time


def get_lat_long(address_full: str):
    if address_full is None:
        return None
    try:
        return fetch_data_from_osm(address_full) or get_nadlan_gov_cords(address_full)
    except (requests.RequestException, IndexError, KeyError, ValueError) as e:
        print(f"Error fetching or processing data: {e}")
        return None
    except requests.ConnectTimeout as e:
        print("Timeout error, retrying....")
        time.sleep(60 * 5)  # maybe needed more...
        return None
    except tenacity.RetryError as e:
        print("retry error, skipping...")
        return None
        # real problem... but it comes back after a while... TODO: fix this


def add_lat_long_to_df(df, column_name="address"):
    lat_long = df[column_name].apply(get_lat_long)
    lat_long = lat_long.apply(pd.Series)
    df = pd.concat([df, lat_long], axis=1)
    return df


def fetch_missing_coordinates(session, limit_per_run, limit_date=None):
    stmt = session.query(NadlanGovTrans).filter(
        NadlanGovTrans.city != None,
        # NadlanGovTrans.address != None,
        NadlanGovTrans.lat == None,
        NadlanGovTrans.long == None,
        ((NadlanGovTrans.treated == None) | (NadlanGovTrans.treated == False))
    ).order_by(NadlanGovTrans.trans_date.desc())

    if limit_per_run is not None:
        stmt = stmt.limit(limit_per_run)
    return stmt.all()


def update_rows_with_coordinates(session, deals):
    n_fixed_deals = 0
    commit_every = 50
    for deal in tqdm(deals, desc="Updating coordinates"):
        address = f"{deal.city} {deal.address}" if deal.address and deal.city else None
        d = get_lat_long(address)
        if d is not None:
            deal.lat = d['lat']
            deal.long = d['long']
            n_fixed_deals += 1
            if n_fixed_deals % commit_every == 0:
                print(f"found! {d['lat']=}, {d['long']=}, {deal.gush_full=}, {deal.trans_date}")
                print(address)
        deal.treated = True
        # After 500 deals must commit to avoid memory issues
        if n_fixed_deals % commit_every == 0:
            session.commit()
    session.commit()
    print(f"Fixed {n_fixed_deals} deals, overall {len(deals)}")
    return n_fixed_deals


def process_missing_coordinates(engine, limit_per_run=500, limit_date=None):
    Session = sessionmaker(bind=engine)
    with Session() as s:
        missing_coords_deals = fetch_missing_coordinates(s, limit_per_run, limit_date)
        n_fixed_deals = update_rows_with_coordinates(s, missing_coords_deals)
    return n_fixed_deals

# process_missing_coordinates()
