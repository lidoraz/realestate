from ext.db_user import User, get_engine_no_vault
from sqlalchemy.orm import Session
from datetime import datetime


def _get_user_data_1():
    return dict(name="test",
                telegram_id=1,
                phone_number=None,  # Ignore phone number for now and insert null
                rent_preferences={
                    'min_price': 3000,
                    'max_price': 7000,
                    'min_rooms': 3,
                    'max_rooms': 4,
                    'asset_status': ['חדש (גרו בנכס)'],
                    'cities': ['אור עקיבא', 'אשקלון'],
                    'must_parking': True,
                    'must_balcony': True,
                    'must_no_agency': None,
                },
                sale_preferences={
                    'min_price': 1000000,
                    'max_price': 3000000,
                    'min_rooms': 3,
                    'max_rooms': 4,
                    'asset_status': [],
                    'cities': ['אילת'],
                    'must_parking': True,
                    'must_balcony': True,
                    'must_no_agency': True,  # should be must be agency
                },
                inserted_at=datetime.now(),
                updated_at=datetime.now())


def test_user_data_1():
    # Create a User instance
    with Session(get_engine_no_vault()) as session:
        new_user = User(**_get_user_data_1())
        # Add the user to the session
        session.add(new_user)
        # Commit the transaction to persist the data
        session.commit()
        session.delete(new_user)
        session.commit()


def test_user_data_2():
    from datetime import datetime
    # Create a User instance
    with Session(get_engine_no_vault()) as session:
        new_user = User(
            name="test",
            telegram_id=2,
            phone_number=None,  # Ignore phone number for now and insert null
            rent_preferences={},
            sale_preferences={},
            inserted_at=datetime.now(),
            updated_at=datetime.now()
        )
        # Add the user to the session
        session.add(new_user)
        # Commit the transaction to persist the data
        session.commit()
        # Query the user by telegram_id
        user_to_delete = session.query(User).filter_by(telegram_id=2).first()
        session.delete(user_to_delete)
        session.commit()


if __name__ == '__main__':
    from ext.env import load_vault

    load_vault()

    test_user_data_1()
    test_user_data_2()
