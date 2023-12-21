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


def get_pg_engine(echo=False, use_vault=True):
    if use_vault:
        load_vault()
    postgres_url = "postgresql://{}:{}@{}:{}/{}".format(os.environ['PGUSER'],
                                                        os.environ['PGPASSWORD'],
                                                        os.environ['PGHOST'],
                                                        os.environ['PGPORT'],
                                                        os.environ['PGDATABASE'])
    eng = create_engine(postgres_url,
                        echo=echo,
                        json_serializer=lambda x: json.dumps(x, ensure_ascii=False))
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
