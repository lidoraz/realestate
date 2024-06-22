import requests
from sqlalchemy.orm import sessionmaker
from scrape_nadlan_gov.insert import RealEstateDeal
from scrape_nadlan_gov.utils import get_lat_long_osm
from tqdm import tqdm


def fetch_missing_coordinates(session, limit_per_run):
    stmt = session.query(RealEstateDeal).filter(
        RealEstateDeal.lat == None,
        RealEstateDeal.long == None,
        RealEstateDeal.treated == False
    )
    if limit_per_run is not None:
        stmt = stmt.limit(limit_per_run)
    return stmt.all()


def update_rows_with_coordinates(session, deals):
    n_fixed_deals = 0
    for deal in tqdm(deals, desc="Updating coordinates"):
        address = f"{deal.city} {deal.address}" if deal.address and deal.city else None
        d = get_lat_long_osm(address)
        if d is not None:
            deal.lat = d['lat']
            deal.long = d['long']
            n_fixed_deals += 1
        deal.treated = True
    session.commit()
    print(f"Fixed {n_fixed_deals} deals, overall {len(deals)}")
    return n_fixed_deals


def process_missing_coordinates(engine, limit_per_run=10_000):
    Session = sessionmaker(bind=engine)
    with Session() as s:
        missing_coords_deals = fetch_missing_coordinates(s, limit_per_run)
        n_fixed_deals = update_rows_with_coordinates(s, missing_coords_deals)
    return n_fixed_deals

# process_missing_coordinates()
