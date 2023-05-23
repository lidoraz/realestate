# from sqlalchemy import create_engine
# import psycopg2
# import os
# from flask import Response, request, jsonify
# import pandas as pd
# import json
# from app_map.sql_scripts import *
#
# assert os.getenv("PGHOST"), "must have all PG related env"
#
#
# def create_connection():
#     # db_url = f'postgresql://{os.getenv("PGUSER")}:{os.getenv("PGPASSWORD")}@{os.getenv("PGHOST")}:{os.getenv("PGPORT")}/{os.getenv("PGDATABASE")}'
#     # engine = create_engine(db_url)
#     conn = psycopg2.connect(
#         host=os.getenv("PGHOST"),
#         port=os.getenv("PGPORT"),
#         dbname=os.getenv("PGDATABASE"),
#         user=os.getenv("PGUSER"),
#         password=os.getenv("PGPASSWORD")
#     )
#     return conn  # engine.connect()
#
#
# # cols_nadlan = ['old_median_avg_meter_price',
# #                'new_median_avg_meter_price', 'old_median_price', 'new_median_price']
#
#
# def get_preprocess(data, sql_query, conn, table_name):
#     sql_query = sql_query.format(table_name=table_name, lat=data['lat'], long=data['long'], dist_km=data['dist_km'])
#     df = pd.read_sql(sql_query, conn)
#     data = df.to_dict(orient="list")
#     return data
#
#
# # @app.route('/get_data', methods=['POST'])
# def get_data():
#     try:
#         data = request.get_json()
#         for v in data.values():
#             assert isinstance(v, (float, int))
#         with create_connection() as conn:
#             data_nadlan = get_preprocess(data, sql_time_series_nadlan, conn, table_name="nadlan_trans")
#             data_recent = get_preprocess(data, sql_time_series_recent, conn, table_name="yad2_forsale_log")
#             data_recent_rent = get_preprocess(data, sql_time_series_recent, conn, table_name="yad2_rent_log")
#         res = dict(data_nadlan=data_nadlan, data_recent=data_recent, data_recent_rent=data_recent_rent)
#         res = json.dumps(res, separators=(',', ':'))
#         return Response(res, mimetype='application/json')
#     except Exception as e:
#         print(e)
#         return jsonify({'error': str("Something happend")}), 400
