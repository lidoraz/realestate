import sqlite3
from tqdm import tqdm
columns = dict(
    ezor="TEXT",
    gush="TEXT",
    tarIska="INTEGER",
    yeshuv="TEXT",
    rechov="TEXT",
    bayit="TEXT",  # can be integer but does know what is the usage
    knisa="TEXT",
    dira="TEXT",  # can be integer but does know what is the usage
    mcirMozhar="INTEGER",
    mcirMorach="INTEGER",
    shetachBruto="INTEGER",
    shetachNeto="INTEGER",
    shnatBniya="INTEGER",
    misHadarim="FLOAT",
    lblKoma="TEXT",  # Does have only 5.0 like and קומת קרקע which needed to be converted to 0.
    misKomot="INTEGER",
    dirotBnyn="INTEGER",
    hanaya="TEXT",
    malit="TEXT",
    sugIska="TEXT",
    tifkudBnyn="TEXT",
    tifkudYchida="TEXT",
    shumaHalakim="TEXT",
    mofaGush="TEXT",
    tava="TEXT",
    mahutZchut="TEXT",
    helekNimkar="TEXT",
    corX="INTEGER",
    corY="INTEGER",
    insertionDate="TIMESTAMP"
)


def convert(value, col_name):
    value = str(value).replace("'", "")  # convert to str and removing bad chars
    dtype = columns[col_name]
    if col_name == "tarIska":
        value = pd.to_datetime(value, format="%d/%m/%Y")
        value = str(value.strftime("%Y%m%d"))
        return value
    if dtype == "INTEGER":
        value = value.replace(",", "") # remove ',' from price
    if dtype == "TEXT" or dtype == "TIMESTAMP":
        value = f"'{value}'"
    return value


def q_create_table(table_name, column_types, primary_keys):
    builder = "CREATE TABLE IF NOT EXISTS '{}' ({} PRIMARY KEY ({}))"
    cols_str = ""
    for name, dtype in column_types.items():
        cols_str += f"{name} {dtype},\n"
    primary_key_str = ','.join(primary_keys)
    builder = builder.format(table_name, cols_str, primary_key_str)
    return builder

#
# create_table_statement = """
# CREATE TABLE IF NOT EXISTS "trans" (
# "ezor" TEXT,
# "gush" TEXT NOT NULL,
# "tarIska" TEXT NOT NULL,
# "yeshuv" TEXT,
# "rechov" TEXT,
# "bayit" TEXT,
# "knisa" TEXT,
# "dira" TEXT,
# "mcirMozhar" TEXT,
# "mcirMorach" TEXT,
# "shetachBruto" TEXT,
# "shetachNeto" TEXT,
# "shnatBniya" TEXT,
# "misHadarim" TEXT,
# "lblKoma" TEXT,
# "misKomot" TEXT,
# "dirotBnyn" TEXT,
# "hanaya" TEXT,
# "malit" TEXT,
# "sugIska" TEXT,
# "tifkudBnyn" TEXT,
# "tifkudYchida" TEXT,
# "shumaHalakim" TEXT,
# "mofaGush" TEXT,
# "tava" TEXT,
# "mahutZchut" TEXT,
# "insertionDate" TIMESTAMP,
# PRIMARY KEY ("gush", "tarIska")
# )
#
# """

import pandas as pd


class DB:
    def __init__(self, path="nadlan.db"):
        self.con = sqlite3.connect(path, check_same_thread=False)
        q_create = q_create_table("trans", columns, ["tarIska", "gush"])
        self.con.execute(q_create)

    def insert_ignore(self, df: pd.DataFrame):
        # Inserts one by one as the limit for using primary key, will also add casting to price and stuff.
        cnt = 0
        for idx, row in tqdm(df.iterrows(), total=len(df)):
            try:
                values = [convert(value, col_name) for col_name, value in row.items()]
                values_str = ','.join(values)
                self.con.execute(f"INSERT INTO trans VALUES({values_str})")
                cnt += 1
            except sqlite3.IntegrityError as e:
                pass
                # can also use INSERT OR IGNORE
                # print("Failed to insert row, Already exists - ", row.tolist())
            except Exception as e:
                print("Error in insertion", e)
        self.con.commit()
        return cnt

    def read(self):
        return pd.read_sql("SELECT * FROM trans", self.con)


if __name__ == '__main__':
    # print(q_create_table("azur", columns, ["gush"]))
    #
    db = DB()
    db_1 = DB("nadlan111.db")
    df = db.read()
    print(df)
    print(db_1.insert_ignore(df))
