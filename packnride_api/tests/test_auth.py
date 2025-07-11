import pytest
from flask import jsonify # Not strictly needed for client tests but useful for constructing expected JSON

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert b"PacknRide API is healthy!" in response.data

def test_register_passenger_success(client):
    """Test successful passenger registration."""
    response = client.post('/auth/register', json={
        "name": "Alice Wonderland",
        "email": "alice@example.com",
        "password": "password123",
        "user_type": "passenger"
    })
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == "User registered successfully"
    assert json_data['user']['email'] == "alice@example.com"
    assert json_data['user']['user_type'] == "passenger"
    assert json_data['user']['id'] is not None

def test_register_driver_success(client):
    """Test successful driver registration."""
    response = client.post('/auth/register', json={
        "name": "Bob The Driver",
        "email": "bob@example.com",
        "password": "passwordDRV",
        "user_type": "driver"
    })
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['user']['email'] == "bob@example.com"
    assert json_data['user']['user_type'] == "driver"

def test_register_duplicate_email(client):
    """Test registration with a duplicate email."""
    user_data = {
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "password": "passwordCB",
        "user_type": "passenger"
    }
    response1 = client.post('/auth/register', json=user_data)
    assert response1.status_code == 201

    response2 = client.post('/auth/register', json=user_data) # Try registering again
    assert response2.status_code == 409 # Conflict
    assert "Email already registered" in response2.get_json()['error']

def test_register_missing_fields(client):
    """Test registration with missing fields."""
    response = client.post('/auth/register', json={
        "name": "Incomplete User",
        "email": "incomplete@example.com"
        # Missing password
    })
    assert response.status_code == 400
    assert "Missing name, email, or password" in response.get_json()['error'] # Or specific missing field

def test_register_invalid_user_type(client):
    """Test registration with an invalid user type."""
    response = client.post('/auth/register', json={
        "name": "Invalid TypeUser",
        "email": "invalidtype@example.com",
        "password": "password123",
        "user_type": "admin" # Invalid type
    })
    assert response.status_code == 400
    assert "Invalid user_type" in response.get_json()['error']

def test_login_success(client, registered_user): # Uses the registered_user fixture
    """Test successful login."""
    login_payload = {
        "email": registered_user['email'],
        "password": registered_user['password']
    }
    response = client.post('/auth/login', json=login_payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "access_token" in json_data
    assert json_data['access_token'] is not None

def test_login_wrong_password(client, registered_user):
    """Test login with an incorrect password."""
    login_payload = {
        "email": registered_user['email'],
        "password": "wrongpassword"
    }
    response = client.post('/auth/login', json=login_payload)
    assert response.status_code == 401 # Unauthorized
    assert "Invalid credentials" in response.get_json()['error']

def test_login_user_not_found(client):
    """Test login for a user that does not exist."""
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "password123"
    }
    response = client.post('/auth/login', json=login_payload)
    assert response.status_code == 404 # Not Found
    assert "Email not found" in response.get_json()['error']

def test_login_missing_fields(client):
    """Test login with missing email or password."""
    response = client.post('/auth/login', json={"email": "test@example.com"})
    assert response.status_code == 400
    assert "Missing email or password" in response.get_json()['error']

    response = client.post('/auth/login', json={"password": "password123"})
    assert response.status_code == 400
    assert "Missing email or password" in response.get_json()['error']

# Example of how to test a protected route (if we had one in auth.py)
# def test_protected_route_requires_token(client):
#     response = client.get('/auth/protected') # Assuming /auth/protected exists and is @jwt_required
#     assert response.status_code == 401 # No token provided

# def test_protected_route_with_valid_token(client, registered_user):
#     headers = {'Authorization': f'Bearer {registered_user["token"]}'}
#     response = client.get('/auth/protected', headers=headers)
#     assert response.status_code == 200
#     assert response.get_json()['logged_in_as']['email'] == registered_user['email']
