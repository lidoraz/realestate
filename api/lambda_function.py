import json
import psycopg2
import os
from sql_scripts import *

example_data_histogram = {'lat': 32.1310648182, 'long': 34.8633406364, 'dist_km': 5, 'n_rooms': 4.5, 'n_months': 6}
example_data_timeseries = {'lat': 32.1310648182, 'long': 34.8633406364, 'dist_km': 1.0}


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
    sql_query = sql_query.format(table_name=table_name, lat=data['lat'], long=data['long'], dist_km=data['dist_km'])
    dict_of_lists = query_dict_of_lists(conn, sql_query)
    return dict_of_lists


def validate_data(data):
    for v in data.values():
        assert isinstance(v, (float, int))


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
    validate_data_has_keys(data, example_data_timeseries.keys())
    with connect() as conn:
        data_nadlan = get_dict_of_lists(data, sql_time_series_nadlan, conn, table_name="nadlan_trans")
        data_recent = get_dict_of_lists(data, sql_time_series_recent, conn, table_name="yad2_forsale_log")
        data_recent_rent = get_dict_of_lists(data, sql_time_series_recent, conn, table_name="yad2_rent_log")
        res = dict(data_nadlan=data_nadlan, data_recent=data_recent, data_recent_rent=data_recent_rent)
    return res


def get_histogram(data):
    validate_data_has_keys(data, example_data_histogram.keys())
    table_name = 'nadlan_trans'
    with connect() as conn:
        sql_query = sql_similar_deals.format(table_name=table_name, lat=data['lat'], long=data['long'],
                                             n_rooms=data['n_rooms'],
                                             dist_km=data['dist_km'],
                                             n_months=data['n_months'])
        print(sql_query)
        dict_of_lists = query_dict_of_lists(conn, sql_query)
        return dict(data_histogram=dict_of_lists)


def lambda_handler(event, context):
    data = json.loads(event['body'])
    method = event['requestContext']['http']['method']
    path = event['requestContext']['http']['path']
    try:
        validate_data(data)
        if method == 'POST' and path == '/timeseries':
            res = get_timeseries(data)
        elif method == 'POST' and path == '/histogram':
            res = get_histogram(data)
        else:
            return {
                'statusCode': 404,
                'body': 'Endpoint not found'
            }
        return {
            'statusCode': 200,
            'body': json.dumps(res, separators=(',', ':'))
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps("Failed")
        }


def _gen_event(data, path):
    event = {}
    data = json.dumps(data)
    event['requestContext'] = {"http": {"method": 'POST', "path": path}}
    event['body'] = data
    return event


def test_api():
    import pandas as pd
    event = _gen_event(example_data_timeseries, '/timeseries')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    print(pd.DataFrame.from_dict(res['data_nadlan']))


def test_hist():
    import pandas as pd
    event = _gen_event(example_data_histogram, '/histogram')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    print(pd.DataFrame.from_dict(res['data_histogram']))


if __name__ == '__main__':
    test_api()
    test_hist()
