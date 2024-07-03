import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Numeric, String, Boolean, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from tqdm import tqdm

Base = declarative_base()


class NadlanGovTrans(Base):
    __tablename__ = 'nadlan_gov_trans'
    trans_date = Column(Date, primary_key=True)
    city = Column(String)
    address = Column(String(255))
    price = Column(Numeric)
    rooms = Column(Numeric)
    floor = Column(Integer, nullable=True)
    n_floors = Column(Integer, nullable=True)
    square_meters = Column(Numeric, nullable=True)
    building_year = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    gush = Column(Integer, nullable=True)
    helka = Column(Integer)
    tat_helka = Column(Integer)
    deal_desc = Column(String)
    price_meter = Column(Numeric)
    street = Column(String)
    house_num = Column(Integer)
    is_new_proj = Column(Boolean)
    project_name = Column(String)
    is_old = Column(Boolean)
    gush_full = Column(String, primary_key=True)
    lat = Column(Numeric)
    long = Column(Numeric)
    treated = Column(Boolean, default=False)
    insertion_time = Column(DateTime)


### not efficent as it must be filterd out by city...
def fetch_existing_primary_keys(session, min_date_back):
    existing_keys = session.query(
        NadlanGovTrans.trans_date,
        NadlanGovTrans.gush_full
    ).filter(NadlanGovTrans.trans_date >= min_date_back).all()
    return set(existing_keys)


def filter_new_data(df, existing_keys):
    def is_existing(row):  # NadlanGovTrans.trans_date
        return (row['trans_date'], row['gush_full']) in existing_keys

    df = df.sort_values('trans_date', ascending=False)
    new_rows = df[~df.apply(is_existing, axis=1)]
    return new_rows


def bulk_insert_new_rows(session, df):
    new_deals = [
        NadlanGovTrans(
            trans_date=row['trans_date'],
            city=row['city'],
            address=row['address'],
            price=row['price'],
            rooms=row['rooms'],
            floor=row['floor'],
            n_floors=row['n_floors'],
            square_meters=row['square_meters'],
            building_year=row['building_year'],
            year_built=row['year_built'],
            gush=row['gush'],
            helka=row['helka'],
            tat_helka=row['tat_helka'],
            deal_desc=row['deal_desc'],
            price_meter=row['price_meter'],
            street=row['street'],
            house_num=row['house_num'],
            is_new_proj=row['is_new_proj'],
            project_name=row['project_name'],
            is_old=row['is_old'],
            gush_full=row['gush_full'],
            lat=None,
            long=None,
            treated=False,
            insertion_time=row['insertion_time']
        ) for index, row in tqdm(df.iterrows(), total=len(df))
    ]
    session.bulk_save_objects(new_deals)
    session.commit()


def insert_new_rows(df, engine, max_days_back):
    sess = sessionmaker(bind=engine)
    min_date_back = (pd.Timestamp.now() - pd.to_timedelta(max_days_back, unit="D")).date()
    df = df[df['trans_date'] >= min_date_back]
    with sess() as session:
        # new_rows['n_floors'] = new_rows['n_floors'].fillna(pd.np.nan)
        existing_keys = fetch_existing_primary_keys(session, min_date_back)
        df_new_rows = filter_new_data(df, existing_keys)
        print(f"Inserted {len(df_new_rows)} new rows to db")
        if not df_new_rows.empty:
            df_new_rows.to_sql(NadlanGovTrans.__tablename__, engine, if_exists='append', index=False)
            session.commit()
            # bulk_insert_new_rows(session, df_new_rows)
        return len(df_new_rows)



def get_engine(DATABASE_URI):
    engine = create_engine(DATABASE_URI)
    return engine


def create_table(engine):
    Base.metadata.create_all(engine)
    return engine


def create_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
