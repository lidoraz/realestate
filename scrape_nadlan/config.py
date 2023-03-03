from sqlalchemy import INTEGER, String, FLOAT, TIMESTAMP, DATE
from pyproj import Transformer

trans_itm_to_wgs84 = Transformer.from_crs(2039, 4326)
primary_keys = ['trans_date', 'gush_full', 'price_declared']
tbl_name = "nadlan_trans"

columns_rename = dict(
    tarIska="trans_date",
    yeshuv="city",
    misHadarim="n_rooms",
    mcirMozhar="price_declared",
    shetachBruto="sq_m_gross",
    shetachNeto="sq_m_net",
    shnatBniya="year_built",
    rechov="street",
    bayit="house_num",  # can be integer but does know what is the usage
    dira="apartment_num",  # can be integer but does know what is the usage
    lblKoma="floor",  # Does have only 5.0 like and קומת קרקע which needed to be converted to 0.
    gush="gush",
    helka="helka",
    misKomot="n_floors",
    dirotBnyn="n_apartments",
    hanaya="parking",
    knisa="entrance",
    malit="elevator",
    sugIska="deal_type",
    tifkudBnyn="house_usage",
    tifkudYchida="apartment_usage",
    shumaHalakim="tax_parts",
    mofaGush="seen_gush",
    tava="tava",
    mahutZchut="right_info",
    helekNimkar="deal_part",
    mcirMorach="price_estimated",
    corX="corX",
    corY="corY",
    lat="lat",
    long="long",
    ezor="area",
    gush_full="gush_full",
    insertionDate="insertion_date"
)
columns_alchemy = dict(
    trans_date=DATE,
    city=String,
    n_rooms=FLOAT,
    price_declared=INTEGER,
    sq_m_gross=INTEGER,
    sq_m_net=INTEGER,
    year_built=INTEGER,
    street=String,
    house_num=String,  # can be integer but does know what is the usage
    apartment_num=String,  # can be integer but does know what is the usage
    floor=String,  # Does have only 5.0 like and קומת קרקע which needed to be converted to 0.
    gush=INTEGER,
    helka=INTEGER,
    n_floors=INTEGER,
    n_apartments=INTEGER,
    parking=String,
    entrance=String,
    elevator=String,
    deal_type=String,
    house_usage=String,
    apartment_usage=String,
    tax_parts=String,
    seen_gush=String,
    tava=String,
    right_info=String,
    deal_part=FLOAT,
    price_estimated=INTEGER,
    corX=INTEGER,
    corY=INTEGER,
    lat=FLOAT,
    long=FLOAT,
    area=String,
    gush_full=String,
    insertion_date=TIMESTAMP
)

assert list(columns_rename.values()) == list(columns_alchemy.keys())
