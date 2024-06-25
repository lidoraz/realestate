import pandas as pd
import os
import json


def process_floors(floors: pd.Series):
    with open("resources/floor_mapper.json", "r") as f:
        floors_dict = json.load(f)
    return floors.map(floors_dict)


#
# cols_to_drop = [['DEALDATETIME', 'DEALDATE', 'FULLADRESS', 'DISPLAYADRESS', 'GUSH',
#                  'DEALNATUREDESCRIPTION', 'ASSETROOMNUM', 'FLOORNO', 'DEALNATURE',
#                  'DEALAMOUNT', 'NEWPROJECTTEXT', 'PROJECTNAME', 'BUILDINGYEAR',
#                  'YEARBUILT', 'BUILDINGFLOORS', 'KEYVALUE', 'TYPE', 'POLYGON_ID',
#                  'TREND_IS_NEGATIVE', 'TREND_FORMAT']]
cols_to_keep = ['trans_date',
                'city',
                'address',
                'price',
                'rooms',
                'floor',
                'n_floors',
                'square_meters',
                'building_year',
                'year_built',
                'gush',
                'helka',
                'tat_helka',
                'deal_desc',
                'price_meter',
                'street',
                'house_num',
                'is_new_proj',
                'project_name',
                'is_old',
                'gush_full',
                'insertion_time']


#     # size = len(df)
#     # df = df[df['DEALNATUREDESCRIPTION'].isin(["דירה בבית קומות", "דירה"])]  # there are more options...
#     # print("len(df) before filtering: ", size, "len(df) after filtering: ", len(df))
def process_nadlan_data(df):
    df['DEALDATETIME'] = pd.to_datetime(df['DEALDATETIME'])
    gush_helka_tat_helka = df['GUSH'].str.split('-')
    df['gush'] = gush_helka_tat_helka.str[0].astype(int)
    df['helka'] = gush_helka_tat_helka.str[1].astype(int)
    df['tat_helka'] = gush_helka_tat_helka.str[2].astype(int)
    df['deal_desc'] = df['DEALNATUREDESCRIPTION']
    df['square_meters'] = df['DEALNATURE'].replace("", None).astype(float)
    df['price'] = df['DEALAMOUNT'].str.replace(",", "").astype(int)
    df['price_meter'] = df['price'] / df['square_meters']
    df['floor'] = process_floors(df['FLOORNO'])
    df['n_floors'] = df['BUILDINGFLOORS']
    df['address'] = df['DISPLAYADRESS'].replace('', None)
    df['street'] = df['address'].str.replace('\d+', '', regex=True).str.strip()
    df['house_num'] = df['address'].str.extract('(\d+)')[0]  # get the first group of digits
    df['rooms'] = df['ASSETROOMNUM'].replace('', None).astype(float)
    df['is_new_proj'] = (df['NEWPROJECTTEXT'] == '1').replace(True, None)
    df['project_name'] = df['PROJECTNAME']
    df['building_year'] = df['BUILDINGYEAR'].astype(float)
    df['year_built'] = df['YEARBUILT'].replace("", None).astype(float)
    df['is_old'] = (df['DEALDATETIME'].dt.year - df['building_year'] > 5) & df['year_built'].isna()
    df['trans_date'] = df['DEALDATETIME'].dt.date
    df['gush_full'] = df['GUSH']
    df['insertion_time'] = pd.Timestamp.now()
    df = df[cols_to_keep]
    assert set(df.columns) == set(cols_to_keep), "Columns mismatch"
    # Replace np.nan with None
    df = df.where(pd.notnull(df), None)

    df = df.sort_values('trans_date', ascending=False)
    return df
