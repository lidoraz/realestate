import json
import psycopg2
import os
from sql_scripts import *
from stats_sql_scripts import *
from today_sql_scripts import *


def query_dict_of_lists(conn, sql_query):
    # Create a cursor object to interact with the database
    with conn.cursor() as cursor:
        cursor.execute(sql_query)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        result_dict = {}
        for column_name in column_names:
            column_index = column_names.index(column_name)
            column_values = [row[column_index] for row in rows]
            result_dict[column_name] = column_values
    return result_dict


def get_dict_of_lists(data, sql_query, conn, table_name):
    sql_query = sql_query.format(table_name=table_name,
                                 lat=data['lat'],
                                 long=data['long'],
                                 rooms=data['rooms'],
                                 dist_km=data['dist_km'])
    dict_of_lists = query_dict_of_lists(conn, sql_query)
    return dict_of_lists


def validate_data(data):
    for v in data.values():
        assert isinstance(v, (float, int, str))


def validate_data_has_keys(data, keys):
    assert len(data.keys()) == len(keys)
    for k in data.keys():
        assert k in keys


def connect():
    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD")
    )


def get_timeseries(data):
    validate_data_has_keys(data, ['lat', 'long', 'dist_km', 'rooms'])
    with connect() as conn:
        data_nadlan = get_dict_of_lists(data, sql_time_series_nadlan, conn, table_name="nadlan_trans")
        data_recent = get_dict_of_lists(data, sql_time_series_recent, conn, table_name="yad2_forsale_log")
        data_recent_rent = get_dict_of_lists(data, sql_time_series_recent, conn, table_name="yad2_rent_log")
        res = dict(data_nadlan=data_nadlan, data_recent=data_recent, data_recent_rent=data_recent_rent)
    return res


def get_histogram(data):
    validate_data_has_keys(data, ['lat', 'long', 'dist_km', 'rooms', 'n_months'])
    table_name = 'nadlan_trans'
    with connect() as conn:
        sql_query = sql_similar_deals.format(table_name=table_name, lat=data['lat'], long=data['long'],
                                             rooms=data['rooms'],
                                             dist_km=data['dist_km'],
                                             n_months=data['n_months'])
        # print(sql_query)
        dict_of_lists = query_dict_of_lists(conn, sql_query)
        return dict(data_histogram=dict_of_lists)


def get_timeseries_recent_quantiles_city(data):
    validate_data_has_keys(data, ['type', 'cities_str'])
    assert len(data['cities_str']) > 0
    cities_str = data['cities_str'].replace('[', '(').replace(']', ')').replace('"', "'")
    with connect() as conn:
        sql_query = sql_time_series_recent_quantiles_city.format(table_name=_get_table(data),
                                                                 cities_str=cities_str)
        dict_of_lists = query_dict_of_lists(conn, sql_query)
        return dict(data_timeseries_recent_quantiles_city=dict_of_lists)


def get_timeseries_recent_quantiles_all(data):
    validate_data_has_keys(data, ['type'])
    with connect() as conn:
        sql_query = sql_time_series_recent_quantiles_all.format(table_name=_get_table(data))
        dict_of_lists = query_dict_of_lists(conn, sql_query)
        return dict(data_timeseries_recent_quantiles_all=dict_of_lists)


def _get_table(data):
    if data['type'] == 'rent':
        table_name = 'yad2_rent_log'
    elif data['type'] == 'sale':
        table_name = 'yad2_forsale_log'
    else:
        raise ValueError("not valid type")
    return table_name


def get_ratio_time_taken_cities(data):
    validate_data_has_keys(data, ['type', 'min_samples', 'days_back'])
    with connect() as conn:
        sql_query = sql_ratio_time_taken_cities.format(table_name=_get_table(data),
                                                       min_samples=data['min_samples'],
                                                       days_back=data['days_back'])
        dict_of_lists = query_dict_of_lists(conn, sql_query)
        return dict(data_ratio_time_taken_cities=dict_of_lists)


def get_today_both_rent_sale(data):
    limit = data.get('limit', 30)
    with connect() as conn:
        sql_query = sql_today_both_rent_sale.format(limit=limit)
        dict_of_lists = query_dict_of_lists(conn, sql_query)
        return dict(data_today_both_rent_sale=dict_of_lists)


def _fail():
    return {'statusCode': 400,
            'body': "Failed"}


def _success(res):
    return {'statusCode': 200,
            'body': json.dumps(res, separators=(',', ':'))}


def _invalid():
    return {'statusCode': 404,
            'body': 'Endpoint not found'}


def lambda_handler(event, context):
    try:
        data = json.loads(event['body'])
        method = event['requestContext']['http']['method']
        path = event['requestContext']['http']['path']
        validate_data(data)
        if method == 'POST' and path == '/timeseries':
            res = get_timeseries(data)
        elif method == 'POST' and path == '/histogram':
            res = get_histogram(data)
        elif method == 'POST' and path == '/timeseries_recent_quantiles_city':
            res = get_timeseries_recent_quantiles_city(data)
        elif method == 'POST' and path == '/timeseries_recent_quantiles_all':
            res = get_timeseries_recent_quantiles_all(data)
        elif method == 'POST' and path == '/ratio_time_taken_cities':
            res = get_ratio_time_taken_cities(data)
        elif method == 'POST' and path == '/today_both_rent_sale':
            res = get_today_both_rent_sale(data)
        else:
            return _invalid()
        return _success(res)
    except Exception as e:
        print("ERROR: lambda_handler::", e.__repr__())
        return _fail()
