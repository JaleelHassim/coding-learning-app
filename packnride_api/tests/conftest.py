import pytest
from app import create_app, users_db, rides_db, id_manager, driving_events_db, driver_scores_db, incident_reports_db
from config import TestingConfig

@pytest.fixture(scope='session')
def app():
    app = create_app(TestingConfig)
    app.config['ENV'] = 'testing'
    app.config['TESTING'] = True
    yield app

@pytest.fixture(scope='function')
def client(app):
    # Reset in-memory 'databases' and ID counters before each test function
    users_db.clear()
    rides_db.clear()
    driving_events_db.clear()
    driver_scores_db.clear()
    incident_reports_db.clear()

    # Reset IDManager counters
    id_manager.user_id_counter = 0
    id_manager.ride_id_counter = 0
    id_manager.driving_event_id_counter = 0
    id_manager.incident_report_id_counter = 0

    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture(scope='function')
def registered_user(client):
    user_data = {
        "name": "Test User", "email": "test@example.com",
        "password": "password123", "user_type": "passenger"
    }
    client.post('/auth/register', json=user_data)
    login_resp = client.post('/auth/login', json={"email": user_data["email"], "password": user_data["password"]})
    token = login_resp.get_json().get('access_token')
    user_obj = users_db.get(user_data["email"])
    user_id = user_obj["id"] if user_obj else None
    return {**user_data, "id": user_id, "token": token}

@pytest.fixture(scope='function')
def registered_driver(client):
    driver_data = {
        "name": "Test Driver", "email": "driver@example.com",
        "password": "password123", "user_type": "driver"
    }
    client.post('/auth/register', json=driver_data)
    login_resp = client.post('/auth/login', json={"email": driver_data["email"], "password": driver_data["password"]})
    token = login_resp.get_json().get('access_token')
    driver_obj = users_db.get(driver_data["email"])
    driver_id = driver_obj["id"] if driver_obj else None
    return {**driver_data, "id": driver_id, "token": token}

@pytest.fixture(scope='function')
def registered_admin(client):
    """Fixture to register and return an admin user's details and token."""
    admin_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "adminpassword",
        "user_type": "passenger", # Admins can be any user_type, is_admin flag is key
        "is_admin": True
    }
    client.post('/auth/register', json=admin_data)

    login_resp = client.post('/auth/login', json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    json_data = login_resp.get_json()
    token = json_data.get('access_token') if json_data else None

    admin_obj = users_db.get(admin_data["email"])
    admin_id = admin_obj.get("id") if admin_obj else None

    return {
        "email": admin_data["email"],
        "password": admin_data["password"],
        "name": admin_data["name"],
        "user_type": admin_data["user_type"],
        "is_admin": True,
        "id": admin_id,
        "token": token
    }
