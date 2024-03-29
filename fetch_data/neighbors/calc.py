import os
import pandas as pd
from ext.env import get_df_from_pg
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
from fetch_data.neighbors.query import *

OUTLIERS_STDS_VAL = 2.0


# # Remove any outliers from the list of data points from each area - data is better since 1 April 2023
# # Data is not clean and there are outliers in the dataset.
def fetch_polygons(q_polygons, table_name):
    q_polygons = q_polygons.format(table_name=table_name)
    return get_df_from_pg(q_polygons)


def fetch_prices(q_prices, table_name, calc_every_x_days=90, min_cnts_for_neighborhood=10):
    q_prices = q_prices.format(calc_every_x_days=calc_every_x_days, table_name=table_name,
                               min_cnt=min_cnts_for_neighborhood)
    return get_df_from_pg(q_prices)


def process(df_prices, df_polygons, metric=None, agg_cols=['city', 'neighborhood']):
    assert metric in ("price_50", "price_meter_50"), metric

    res = pd.Series(dtype=float)
    cnts = {}
    agg_cols = agg_cols[0] if len(agg_cols) == 1 else agg_cols
    for g, x in df_prices.groupby(agg_cols):
        res = pd.concat([res, x[metric].pct_change()])
        cnts[g] = len(x)
    res = res.rename("pct_change").sort_index()
    df = df_prices.join(res)
    ## ADD ALL METRICS HERE TO CALCLUATE
    # df_last = df.groupby(agg_cols).agg(metric=(metric, 'last'),
    #                                    pct_change=("pct_change", 'last'),
    #                                    cnt=('cnt', 'last'),
    #                                    metric_lst=(metric, list),
    #                                    period_lst=('start_date', list),
    #                                    n_periods=('start_date', 'size')).query('not pct_change.isnull()').reset_index()
    df_last = df.groupby(agg_cols)[[metric, "pct_change", 'cnt']].last().reset_index()

    df_all = df_last.merge(df_polygons, left_on=agg_cols, right_on=agg_cols)
    cords = remove_outliers(df_all, OUTLIERS_STDS_VAL)
    df_all['geometry'] = [Polygon(list_points) for list_points in cords]
    return df_all


def remove_outliers(df_all, stds_val=1.0):
    cords = [(tuple(zip(x, y))) for x, y in zip(df_all['list_long'], df_all['list_lat'])]
    stds_lat = df_all['list_lat'].apply(lambda x: np.std(x))
    mean_lat = df_all['list_lat'].apply(lambda x: np.mean(x))
    stds_long = df_all['list_long'].apply(lambda x: np.std(x))
    mean_long = df_all['list_long'].apply(lambda x: np.mean(x))
    cords_adj = []
    for idx, city_neightbor_cords in enumerate(cords):
        cords_adj.append(
            [point for point in city_neightbor_cords if point[1] - mean_lat[idx] < stds_lat[idx] * stds_val and
             point[0] - mean_long[idx] < stds_long[idx] * stds_val])
    return cords_adj


def create_geodf(df_all, metric, agg_cols=['city', 'neighborhood'], alpha=0.7):
    gdf = gpd.GeoDataFrame(df_all, geometry='geometry', crs=3857)  # crs=3857
    # gdf = gdf.dissolve(['city', 'neighborhood']).simplify(10, preserve_topology=True).reset_index().rename(columns={0: "geometry"})
    # gdf['geometry'] = gdf['geometry'].apply(lambda x: x.exterior.coords)
    # Must have 0.14 version
    gdf['geometry'] = gdf.concave_hull(alpha)
    gdf = gdf[gdf.geom_type == 'Polygon']

    gdf['n_points'] = gdf['geometry'].apply(lambda x: len(x.exterior.coords))
    gdf['area'] = gdf.area  # / 10**6
    gdf["type"] = "C" if len(
        agg_cols) == 1 else "N"  # '_'.join(agg_cols)  # can add this for custom pct detection by type
    gdf['tooltip'] = ""
    for c in agg_cols:
        gdf['tooltip'] += gdf[c].astype(str) + '</br>'
    gdf['tooltip'] += "(" + gdf['cnt'].astype(str) + ')</br>' \
                      + (
                          "מחיר למטר" if metric == "price_meter_50" else "מחיר חציוני" if metric == "price_50" else "") + "</br>" \
                      + gdf[metric].apply(lambda x: f"{x:,.0f}") + "(" + gdf['pct_change'].apply(
        lambda x: f"{x:0.2%}") + ")"

    # gdf['centroid'] = gdf.centroid
    gdf = gdf.sort_values('n_points', ascending=False)
    return gdf


def save_to_geojson(gdf, name, path=""):
    file_name = os.path.join(path, f"changes_last_polygon_{name}.json")
    gdf.to_file(file_name, driver="GeoJSON", index=False)
    from ext.publish import put_object_in_bucket
    put_object_in_bucket(file_name)


def run_neighbors():
    print("run_neighbors")
    calc_every_x_days = 90
    min_cnts_for_neighborhood = 10
    alpha_concave_hull = 0.5
    path = f'resources'
    table_names = ["yad2_forsale_log", "yad2_rent_log"]
    agg_cols_lst = [['city'], ['city', 'neighborhood']]

    for table_name in table_names:
        for agg_cols in agg_cols_lst:
            print(table_name, agg_cols)
            if agg_cols == ['city', 'neighborhood']:
                q_polygons = q_polygons_city_neighborhood
                q_prices = q_prices_city_neighborhood
            elif agg_cols == ['city']:
                q_polygons = q_polygons_city
                q_prices = q_prices_city
            else:
                raise ValueError(f"Not Valid! {agg_cols}")

            metric = "price_50" if table_name == 'yad2_rent_log' else "price_meter_50"

            output_name = table_name.split('_')[1] + "_" + "_".join(agg_cols)

            df_polygons = fetch_polygons(q_polygons, table_name)
            df_prices = fetch_prices(q_prices, table_name, calc_every_x_days, min_cnts_for_neighborhood)
            df_all = process(df_prices, df_polygons, metric, agg_cols)

            df_all = df_all[[*agg_cols, metric, 'pct_change', 'cnt', 'geometry']]
            gdf = create_geodf(df_all, metric, agg_cols, alpha=alpha_concave_hull)
            save_to_geojson(gdf, output_name, path)


if __name__ == '__main__':
    from os.path import dirname

    file_dir = dirname(dirname(dirname(__file__)))
    os.chdir(file_dir)
    print(file_dir)
    run_neighbors()
