from ext.env import get_df_from_pg


def get_bad_locations(asset_type):
    sql = f"""
        select
        city,
        lat,
        long,
        lat::varchar || long::varchar as latlong,
        count(*)                      as cnt_same
        from yad2_{asset_type}_today
        where lat is not null and long is not null
        group by city, lat, long
        having count(*) > 50
    """
    df = get_df_from_pg(sql)
    return df


def filter_bad_loc_assets(df, asset_type):
    df_bad_loc = get_bad_locations(asset_type)
    bad_locs = df_bad_loc['latlong'].tolist()
    latlong = df['lat'].astype(str) + df['long'].astype(str)
    df_f = df[~latlong.isin(bad_locs)]
    return df_f


def get_model_cols_n_cat():
    must_have_cols = ['price', 'lat', 'long']
    bool_cols = [
        'is_active',
        'is_agency',
        'balconies',
        'renovated',
        'asset_exclusive_declaration',
        'air_conditioner',
        'bars',
        'elevator',
        'boiler',
        'accessibility',
        'shelter',
        'warhouse',
        'tadiran_c',
        'furniture',
        'flexible_enter_date',
        'kosher_kitchen',
        'housing_unit',
        'is_keycrap',
        'is_city_renew',
        'is_tama',
        'is_tama_before',
        'is_tama_after',
        'is_zehut'
    ]
    num_cols = [
        # 'price_diff',
        # 'avg_price_chg',

        'std_price_chg',
        'price_pct',
        'n_changes',
        'rooms', 'square_meters', 'garden_area', 'floor',
        'parking',
        'number_of_floors', 'n_images',
        'days_last_updated',
        'days_in_market',
        'week_num_from_start']
    cat_features = ['asset_type', 'city', 'asset_status', 'neighborhood', ]
    cols = must_have_cols + bool_cols + num_cols + cat_features
    return cols, cat_features
