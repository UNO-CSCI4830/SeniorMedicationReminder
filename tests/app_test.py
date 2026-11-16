import pytest

# Testing whether the signup form is being submitted into the database
def test_usersignup_database(client, db):

    signup_table = {
        'firstname': 'Test',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }

    response = client.post('/signup', data=signup_table)
    assert response.status_code == 302

    user = db.execute("SELECT * FROM users WHERE email = 'test@example.com'").fetchone()

    assert user is not None
    assert user['first_name'] == 'Test'
    assert user['email'] == 'test@example.com'
    assert user['password_hash'] != 'password123'

# Testing signup form for missing fields
@pytest.mark.parametrize("missing_field", ['firstname', 'email', 'password', 'confirm_password'])
def test_missing_signup_information(client, db, missing_field):
    signup_table = {
        'firstname': 'Test',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }

    signup_table[missing_field] = ""
    response = client.post('/signup', data=signup_table)

    assert response.status_code == 200
    assert db.execute("SELECT * FROM users WHERE email = 'test@example.com'")

    if missing_field == "confirm_password":
        assert b"Passwords do not match." in response.data
    else:
        assert b"Please fill in all required fields." in response.data

# Testing existing email reponse and that it doesn't overwrite original user in database
def test_duplicate_email(client, db):
    db.execute("INSERT INTO users (first_name, email, password_hash) VALUES (?, ?, ?)",
        ('TestUser', 'test@example.com', 'password321')
    )

    signup_table = {
        'firstname': 'NewUser',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password 123'
    }

    response = client.post('/signup', data=signup_table)
    assert response.status_code == 200

    assert b"An account with that email already exist."
    user = db.execute("SELECT * FROM users WHERE email = 'test@example.com'").fetchone()
    assert user is not None
    assert user['first_name'] == 'TestUser'