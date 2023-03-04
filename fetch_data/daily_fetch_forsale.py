from fetch_data.daily_fetch import process_tables, add_distance, add_ai_price
from fetch_data.utils import get_connetor, get_today, get_price_hist, get_nadlan

if __name__ == '__main__':
    conn = get_connetor()
    type = 'forsale'
    df_hist = get_price_hist(type, conn)
    df_today = get_today(type, conn)
    # os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df = process_tables(df_today, df_hist)
    df = add_distance(df)
    df = add_ai_price(df, type)
    #
    path = f'resources/yad2_{type}_df.pk'
    df.to_pickle(path)

    df = get_nadlan(conn, 180)
    df.to_pickle("resources/df_nadlan_recent.pk")



    # print()
    # import pandas as pd
    # df = pd.read_pickle(path)
    #
    # df = add_ai_price(df)
    # print(len(df))
