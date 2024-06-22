import unittest
from unittest import mock
import pandas as pd
from scrape_nadlan_gov.insert import get_engine, create_table, insert_new_rows, create_session, RealEstateDeal, Base
from scrape_nadlan_gov.update_cords import process_missing_coordinates


def load_new_data():
    # Placeholder for example data
    new_data = {
        'trans_date': ['2024-06-20', '2024-06-20'],
        'city': ['CityA', 'CityB'],
        'address': ['Address 1', 'Address 2'],
        'price': [500000, 750000],
        'rooms': [4, 5],
        'floor': [1, 2],
        'n_floors': [5, 10],
        'square_meters': [100, 150],
        'building_year': [2000, 2010],
        'year_built': [2000, 2010],
        'gush': [12345, 12346],
        'helka': [1, 2],
        'tat_helka': [1, 1],
        'deal_desc': ['Deal 1', 'Deal 2'],
        'price_meter': [5000, 5000],
        'street': ['Street 1', 'Street 2'],
        'house_num': [1, 2],
        'is_new_proj': [True, False],
        'project_name': ['Project 1', 'Project 2'],
        'is_old': [False, True],
        'gush_full': ['12345-1-1', '12346-2-1'],
        'lat': [None, None],
        'long': [None, None],
        'insertion_time': ['2024-06-20T12:22:11', '2024-06-20T23:22:11']
    }

    new_data_df = pd.DataFrame(new_data)
    new_data_df['trans_date'] = pd.to_datetime(new_data_df['trans_date']).apply(lambda x: x.date())
    new_data_df['insertion_time'] = pd.to_datetime(new_data_df['insertion_time'])
    return new_data_df


DATABASE_URI = 'sqlite:///real_estate_deals.db'


class TestFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uri = DATABASE_URI

    def setUp(cls):
        DATABASE_URI = 'sqlite:///real_estate_deals.db'
        engine = get_engine(cls.uri)
        create_table(engine)

    def test_create_insert(cls):
        new_data_df = load_new_data()
        engine = get_engine(cls.uri)
        n_new = insert_new_rows(new_data_df, engine)
        assert n_new == 2
        import pandas as pd
        session = create_session(engine)
        df_f = pd.read_sql(session.query(RealEstateDeal).statement, session.bind)
        print(df_f)

    def test_exist(cls):
        new_data_df = load_new_data()
        engine = get_engine(cls.uri)
        n_new = insert_new_rows(new_data_df, engine)
        assert n_new == 2
        n_new = insert_new_rows(new_data_df, engine)
        assert n_new == 0

    def test_fix_cords(cls):
        mock.patch('scrape_nadlan_gov.utils.get_lat_long_osm', return_value={'lat': 32.0, 'long': 34.0})
        new_data_df = load_new_data()
        engine = get_engine(cls.uri)
        n_new = insert_new_rows(new_data_df, engine)
        assert n_new == 2
        process_missing_coordinates(engine)
        session = create_session(engine)
        df = pd.read_sql(session.query(RealEstateDeal).statement, session.bind)
        assert len(df) == 2
        assert df['lat'].notnull().all()
        assert df['long'].notnull().all()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        os.remove('real_estate_deals.db')

    def tearDown(cls):
        engine = get_engine(cls.uri)
        Base.metadata.tables['real_estate_deals'].drop(engine)
