import pytest

def test_request_ride_success(client, registered_user):
    """Test successful ride request by a passenger."""
    headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {
        "pickup_location": "1 Main St",
        "dropoff_location": "10 End Rd"
    }
    response = client.post('/api/rides/request', headers=headers, json=ride_payload)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == "Ride requested successfully"
    assert json_data['ride']['pickup_location'] == "1 Main St"
    assert json_data['ride']['status'] == "pending"
    assert json_data['ride']['passenger_id'] == registered_user['id']

def test_request_ride_by_driver_fails(client, registered_driver):
    """Test that a driver cannot request a ride."""
    headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    ride_payload = {
        "pickup_location": "Driver Home",
        "dropoff_location": "Driver Work"
    }
    response = client.post('/api/rides/request', headers=headers, json=ride_payload)
    assert response.status_code == 403
    assert "Only passengers can request rides" in response.get_json()['error']

def test_request_ride_missing_location(client, registered_user):
    """Test ride request with missing location data."""
    headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "1 Main St"} # Missing dropoff
    response = client.post('/api/rides/request', headers=headers, json=ride_payload)
    assert response.status_code == 400
    assert "Missing pickup_location or dropoff_location" in response.get_json()['error']

def test_get_ride_details_success(client, registered_user):
    """Test passenger getting their ride details."""
    headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    # First, request a ride
    ride_payload = {"pickup_location": "Origin", "dropoff_location": "Destination"}
    post_response = client.post('/api/rides/request', headers=headers, json=ride_payload)
    assert post_response.status_code == 201
    ride_id = post_response.get_json()['ride']['id']

    # Get details for that ride
    get_response = client.get(f'/api/rides/{ride_id}', headers=headers)
    assert get_response.status_code == 200
    json_data = get_response.get_json()
    assert json_data['id'] == ride_id
    assert json_data['passenger_id'] == registered_user['id']

def test_get_ride_details_unauthorized(client, registered_user, registered_driver):
    """Test that a user cannot get details of a ride they are not part of."""
    # Passenger 1 requests a ride
    passenger1_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "P1 Start", "dropoff_location": "P1 End"}
    post_response = client.post('/api/rides/request', headers=passenger1_headers, json=ride_payload)
    assert post_response.status_code == 201
    ride_id = post_response.get_json()['ride']['id']

    # Driver (not yet assigned) tries to access
    driver_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    get_response_driver = client.get(f'/api/rides/{ride_id}', headers=driver_headers)
    assert get_response_driver.status_code == 403 # Forbidden as driver is not yet assigned

def test_accept_ride_success(client, registered_user, registered_driver):
    """Test successful ride acceptance by a driver."""
    # Passenger requests a ride
    passenger_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "Cafe", "dropoff_location": "Home"}
    post_response = client.post('/api/rides/request', headers=passenger_headers, json=ride_payload)
    ride_id = post_response.get_json()['ride']['id']

    # Driver accepts the ride
    driver_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    accept_response = client.post(f'/api/rides/{ride_id}/accept', headers=driver_headers)
    assert accept_response.status_code == 200
    json_data = accept_response.get_json()
    assert json_data['message'] == "Ride accepted successfully"
    assert json_data['ride']['status'] == "accepted"
    assert json_data['ride']['driver_id'] == registered_driver['id']

    # Verify passenger can also see the update
    get_ride_resp = client.get(f'/api/rides/{ride_id}', headers=passenger_headers)
    assert get_ride_resp.get_json()['driver_id'] == registered_driver['id']
    assert get_ride_resp.get_json()['status'] == 'accepted'


def test_accept_ride_by_passenger_fails(client, registered_user):
    """Test that a passenger cannot accept a ride."""
    passenger_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "A", "dropoff_location": "B"}
    post_response = client.post('/api/rides/request', headers=passenger_headers, json=ride_payload)
    ride_id = post_response.get_json()['ride']['id']

    accept_response = client.post(f'/api/rides/{ride_id}/accept', headers=passenger_headers)
    assert accept_response.status_code == 403
    assert "Only drivers can accept rides" in accept_response.get_json()['error']

def test_accept_already_accepted_ride_fails(client, registered_user, registered_driver):
    """Test accepting a ride that is already accepted by another driver."""
    # Passenger requests
    passenger_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "X", "dropoff_location": "Y"}
    post_response = client.post('/api/rides/request', headers=passenger_headers, json=ride_payload)
    ride_id = post_response.get_json()['ride']['id']

    # First driver accepts
    driver1_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    client.post(f'/api/rides/{ride_id}/accept', headers=driver1_headers)

    # Second driver (need another fixture or register another driver)
    other_driver_data = {"name": "Driver Two", "email": "driver2@example.com", "password": "pwd", "user_type": "driver"}
    client.post('/auth/register', json=other_driver_data)
    login_resp = client.post('/auth/login', json={"email": "driver2@example.com", "password": "pwd"})
    other_driver_token = login_resp.get_json()['access_token']
    driver2_headers = {'Authorization': f'Bearer {other_driver_token}'}

    accept_response = client.post(f'/api/rides/{ride_id}/accept', headers=driver2_headers)
    assert accept_response.status_code == 409 # Conflict

def test_update_ride_status_driver_success(client, registered_user, registered_driver):
    """Test driver successfully updating ride status."""
    passenger_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "Start", "dropoff_location": "Finish"}
    post_response = client.post('/api/rides/request', headers=passenger_headers, json=ride_payload)
    ride_id = post_response.get_json()['ride']['id']

    driver_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    client.post(f'/api/rides/{ride_id}/accept', headers=driver_headers) # Driver accepts

    # Driver updates status
    status_payload = {"status": "en_route_pickup"}
    update_response = client.put(f'/api/rides/{ride_id}/status', headers=driver_headers, json=status_payload)
    assert update_response.status_code == 200
    assert update_response.get_json()['ride']['status'] == "en_route_pickup"

    status_payload = {"status": "arrived_pickup"}
    update_response = client.put(f'/api/rides/{ride_id}/status', headers=driver_headers, json=status_payload)
    assert update_response.status_code == 200

    status_payload = {"status": "started"}
    update_response = client.put(f'/api/rides/{ride_id}/status', headers=driver_headers, json=status_payload)
    assert update_response.status_code == 200

    status_payload = {"status": "completed"}
    update_response = client.put(f'/api/rides/{ride_id}/status', headers=driver_headers, json=status_payload)
    assert update_response.status_code == 200
    assert update_response.get_json()['ride']['status'] == "completed"
    assert update_response.get_json()['ride']['fare'] is not None


def test_update_ride_status_passenger_cancel_success(client, registered_user, registered_driver):
    """Test passenger successfully cancelling a ride."""
    passenger_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    ride_payload = {"pickup_location": "Uptown", "dropoff_location": "Downtown"}
    post_response = client.post('/api/rides/request', headers=passenger_headers, json=ride_payload)
    ride_id = post_response.get_json()['ride']['id']

    # Passenger cancels before driver accepts
    status_payload = {"status": "cancelled"}
    update_response = client.put(f'/api/rides/{ride_id}/status', headers=passenger_headers, json=status_payload)
    assert update_response.status_code == 200
    assert update_response.get_json()['ride']['status'] == "cancelled"

    # New ride for testing cancellation after driver accepts
    post_response_2 = client.post('/api/rides/request', headers=passenger_headers, json=ride_payload) # Renamed to avoid conflict
    ride_id_2 = post_response_2.get_json()['ride']['id']
    driver_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    client.post(f'/api/rides/{ride_id_2}/accept', headers=driver_headers) # Driver accepts

    update_response_2 = client.put(f'/api/rides/{ride_id_2}/status', headers=passenger_headers, json=status_payload)
    assert update_response_2.status_code == 200
    assert update_response_2.get_json()['ride']['status'] == "cancelled"


def test_update_ride_status_invalid_transition(client, registered_user, registered_driver):
    """Test invalid status transition by driver."""
    passenger_headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    post_response = client.post('/api/rides/request', headers=passenger_headers, json={"pickup_location":"A","dropoff_location":"B"})
    ride_id = post_response.get_json()['ride']['id']

    driver_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    # Ride is 'pending', driver tries to set to 'started' (invalid without accepting first)
    status_payload = {"status": "started"}
    update_response = client.put(f'/api/rides/{ride_id}/status', headers=driver_headers, json=status_payload)
    assert update_response.status_code == 403


def test_get_nearby_drivers_mocked(client, registered_user, registered_driver):
    """Test getting mocked nearby drivers."""
    # Ensure registered_driver is actually created by calling the fixture
    # The registered_driver fixture already handles registration and login.
    # We need its ID for assertion.
    driver_id = registered_driver['id']

    headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    response = client.get('/api/drivers/nearby', headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "available_drivers" in json_data
    # Check if the registered_driver (who is not on a ride) is in the list
    found_driver = any(d['id'] == driver_id for d in json_data['available_drivers'])
    assert found_driver == True


def test_estimate_fare_mocked(client, registered_user):
    """Test getting mocked fare estimation."""
    headers = {'Authorization': f'Bearer {registered_user["token"]}'}
    fare_payload = {"pickup_location": "Long Street", "dropoff_location": "Short Avenue"}
    response = client.post('/api/rides/estimate_fare', headers=headers, json=fare_payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "estimated_fare_rand" in json_data
    assert "currency" in json_data and json_data['currency'] == "ZAR"
