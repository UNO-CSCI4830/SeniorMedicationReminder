#Initialize Isolated flask app and database for testing

import pytest
from app import create_app
from database import get_db, init_db

@pytest.fixture(scope='function')
def app(tmp_path):
    test_db_path = tmp_path / "test.db"

    app = create_app({
        'TESTING': True,
        'DATABASE': str(test_db_path),
        'SECRET_KEY': 'test_key',
        'REMINDER_TIMEZONE': 'America/Omaha'
        })

    with app.app_context():
        init_db(app)

    yield app

# Test client for app to get HTTP requests
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    with app.app_context():
        connect_db = get_db()
        yield get_db()
        connect_db.close()

