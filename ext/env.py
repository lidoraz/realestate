import json
import os
from sqlalchemy import create_engine


def get_default_path():
    path = os.path.join(os.path.expanduser('~'),
                        '.ssh',
                        "creds_postgres.json")
    return path


def load_vault(path=get_default_path()):
    with open(path) as f:
        c = json.load(f)
    for k, v in c.items():
        os.environ[k] = str(v)


def get_pg_engine():
    load_vault()
    eng = create_engine(
        f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}")
    return eng


def get_df_from_pg(query):
    import pandas as pd
    from sqlalchemy import text
    eng = get_pg_engine()
    with eng.connect() as conn:
        return pd.read_sql(text(query), conn)


def get_query(file):
    with open(file, 'r') as f:
        return f.read()
