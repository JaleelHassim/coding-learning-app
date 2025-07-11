import pytest
from app import create_app, users_db, rides_db, id_manager
from config import TestingConfig # Make sure TestingConfig is appropriate

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    # Ensure a clean state for each test session if needed,
    # though for module/function scope fixtures, this might be handled differently.
    # For in-memory dbs, they might persist across a session if not careful.
    app = create_app(TestingConfig)

    # Ensure FLASK_ENV is set to testing for the app context
    app.config['ENV'] = 'testing' # Redundant if TestingConfig sets it, but good for clarity
    app.config['TESTING'] = True

    # If you need to clean up global in-memory stores between test *sessions*
    # you could do it here, but typically test isolation is preferred at a finer grain.
    # For this example, we'll rely on test functions to manage state or use function-scoped fixtures
    # if state needs to be reset for every test.

    yield app # Provide the app instance

@pytest.fixture(scope='function') # Use function scope to get a fresh client and clean dbs for each test
def client(app):
    """A test client for the app."""
    # Reset in-memory 'databases' and ID counters before each test function
    users_db.clear()
    rides_db.clear()
    # Reset ID counters by creating a new IDManager instance or resetting its internal counters
    # For simplicity, let's re-initialize its counters if possible, or replace the instance.
    # Accessing id_manager directly from app might be tricky if it's not exposed.
    # The simplest way for this example:
    id_manager.user_id_counter = 0
    id_manager.ride_id_counter = 0

    with app.test_client() as client:
        with app.app_context(): # Push an application context
            yield client

# You can add more fixtures here, e.g., for creating authenticated users
@pytest.fixture(scope='function')
def registered_user(client):
    """Fixture to register and return a user's details and token."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "user_type": "passenger"
    }
    client.post('/auth/register', json=user_data) # Register the user

    # Login to get token
    login_resp = client.post('/auth/login', json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_resp.get_json()['access_token']

    # Return user_data along with id (which we don't easily get back from register)
    # and the token. For tests, we might need the user's ID.
    # users_db is keyed by email, so we can retrieve the registered user.
    user_obj = users_db.get("test@example.com")
    user_id = user_obj["id"] if user_obj else None # Handle case where user might not be found if test setup fails

    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "name": user_data["name"],
        "user_type": user_data["user_type"],
        "id": user_id,
        "token": token
    }

@pytest.fixture(scope='function')
def registered_driver(client):
    """Fixture to register and return a driver's details and token."""
    driver_data = {
        "name": "Test Driver",
        "email": "driver@example.com",
        "password": "password123",
        "user_type": "driver"
    }
    client.post('/auth/register', json=driver_data)

    login_resp = client.post('/auth/login', json={
        "email": "driver@example.com",
        "password": "password123"
    })
    token = login_resp.get_json()['access_token']
    driver_obj = users_db.get("driver@example.com")
    driver_id = driver_obj["id"] if driver_obj else None

    return {
        "email": driver_data["email"],
        "password": driver_data["password"],
        "name": driver_data["name"],
        "user_type": driver_data["user_type"],
        "id": driver_id,
        "token": token
    }
