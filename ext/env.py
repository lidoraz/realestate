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
