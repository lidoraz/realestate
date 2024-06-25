import os

from sqlalchemy import Column, BigInteger, String, JSON, DateTime, TIMESTAMP, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from ext.env import get_pg_engine
import sqlalchemy
import logging

Base = declarative_base()


class User(Base):
    __tablename__ = 'realestate_telegram_users'
    # Set telegram_id as the primary key
    telegram_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    phone_number = Column(String)
    sale_preferences = Column(JSON)
    rent_preferences = Column(JSON)
    inserted_at = Column(DateTime)
    updated_at = Column(DateTime)


# {ip, telegram_id, asset_id, asset_type, url, time, clicks, user_agent})"
class UserActivity(Base):
    __tablename__ = 'realestate_user_activity'
    rec_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    dt = Column(TIMESTAMP)
    asset_id = Column(String)
    asset_type = Column(String)
    endpoint = Column(String)
    ip = Column(String)
    user_agent = Column(String)
    clicks = Column(Integer)
    session_rn = Column(Integer)


def get_engine_no_vault():
    is_echo = os.getenv('PRODUCTION') != 'TRUE'
    engine = get_pg_engine(is_echo, use_vault=False)
    return engine


def create_all():
    engine = get_engine_no_vault()
    # User.__table__.drop(bind=engine)
    # Create the tables
    Base.metadata.create_all(engine)


def _get_user_record(session, user_data):
    user_record = session.query(User).filter_by(telegram_id=user_data['telegram_id']).first()
    return user_record


def _add_user_record(session, user_data):
    session.add(User(**user_data))
    session.commit()


def add_user_activity_records(user_data_lst):
    if not os.getenv("PRODUCTION", False):
        return -1
    with Session(get_engine_no_vault()) as session:
        try:
            cnt = _add_user_activity_records(session, user_data_lst)
            logging.info(f'Added {cnt} user activity records')
            return cnt
        except Exception as e:
            session.rollback()
            logging.error("add_user_activity_records:", e)
            return -1


def _add_user_activity_records(session, user_data_lst):
    assert isinstance(user_data_lst, list)
    cnt = 0
    for user_data in user_data_lst:
        session.add(UserActivity(**user_data))
        cnt += 1
    session.commit()
    return cnt


def _update(session, user_record, user_data):
    # Update the original user with values from the updated user
    for key, value in user_data.items():
        # Exclude some internal attributes
        if key != 'inserted_at':
            setattr(user_record, key, value)
    session.commit()


def insert_or_update_user(user_data):
    with Session(get_engine_no_vault()) as session:
        try:
            user_record = _get_user_record(session, user_data)
            if user_record is None:
                _add_user_record(session, user_data)
                return "insert"
            else:
                _update(session, user_record, user_data)
                return "update"
        except sqlalchemy.exc.SQLAlchemyError as e:
            session.rollback()
            print(e)
            return "err"


def insert_new_user(user_data):
    with Session(get_engine_no_vault()) as session:
        try:
            session.add(User(**user_data))
            session.commit()
            return True
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            print(e)
            return False


def select_all():
    import pandas as pd
    with Session(get_engine_no_vault()) as session:
        return pd.read_sql(session.query(User).statement, session.bind)
