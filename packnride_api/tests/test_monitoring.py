import pytest
import datetime
from app import driving_events_db, driver_scores_db, incident_reports_db # For direct inspection if needed

# --- Test Driving Event Endpoints ---

def test_log_driving_event_by_admin(client, registered_admin, registered_driver):
    """Admin logs a driving event for a driver."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    event_data = {
        "driver_id": registered_driver["id"],
        "event_type": "speeding",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "location_lat": -25.7479,
        "location_lon": 28.2293,
        "details": {"speed_kmh": 100, "limit_kmh": 60}
    }
    response = client.post('/api/monitoring/events', headers=headers, json=event_data)
    assert response.status_code == 201
    json_resp = response.get_json()['event']
    assert json_resp['driver_id'] == registered_driver["id"]
    assert json_resp['event_type'] == "speeding"

def test_log_driving_event_by_driver_self(client, registered_driver):
    """Driver logs their own driving event."""
    headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    event_data = {
        "driver_id": registered_driver["id"], # Must match self
        "event_type": "harsh_braking",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "location_lat": -25.7470,
        "location_lon": 28.2290,
        "details": {"g_force": 0.8}
    }
    response = client.post('/api/monitoring/events', headers=headers, json=event_data)
    assert response.status_code == 201
    assert response.get_json()['event']['event_type'] == "harsh_braking"

def test_log_driving_event_unauthorized(client, registered_user, registered_driver):
    """Non-admin passenger tries to log event for another driver."""
    headers = {'Authorization': f'Bearer {registered_user["token"]}'} # Passenger token
    event_data = {"driver_id": registered_driver["id"], "event_type": "test", "timestamp": datetime.datetime.utcnow().isoformat(), "location_lat":0.0, "location_lon":0.0}
    response = client.post('/api/monitoring/events', headers=headers, json=event_data)
    assert response.status_code == 403 # Forbidden

def test_get_driver_events_by_admin(client, registered_admin, registered_driver):
    """Admin gets events for a specific driver."""
    # Log an event first
    admin_headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    client.post('/api/monitoring/events', headers=admin_headers, json={
        "driver_id": registered_driver["id"], "event_type": "idling",
        "timestamp": datetime.datetime.utcnow().isoformat(), "location_lat":0.0, "location_lon":0.0
    })

    response = client.get(f'/api/monitoring/drivers/{registered_driver["id"]}/events', headers=admin_headers)
    assert response.status_code == 200
    json_resp = response.get_json()
    assert isinstance(json_resp['events'], list)
    assert len(json_resp['events']) > 0
    assert json_resp['events'][0]['event_type'] == "idling"

def test_get_driver_events_by_self(client, registered_driver):
    """Driver gets their own events."""
    driver_headers = {'Authorization': f'Bearer {registered_driver["token"]}'}
    client.post('/api/monitoring/events', headers=driver_headers, json={
        "driver_id": registered_driver["id"], "event_type": "cornering",
        "timestamp": datetime.datetime.utcnow().isoformat(), "location_lat":0.0, "location_lon":0.0
    })
    response = client.get(f'/api/monitoring/drivers/{registered_driver["id"]}/events', headers=driver_headers)
    assert response.status_code == 200
    assert len(response.get_json()['events']) > 0

# --- Test Driver Performance Score Endpoints ---

def test_get_driver_score_initial(client, registered_admin, registered_driver):
    """Admin gets initial (empty) score for a driver."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    response = client.get(f'/api/monitoring/drivers/{registered_driver["id"]}/score', headers=headers)
    assert response.status_code == 200
    json_resp = response.get_json()
    assert json_resp['overall_safety_score'] is None
    assert "No score data available yet" in json_resp['feedback_summary']

def test_update_and_get_driver_score_by_admin(client, registered_admin, registered_driver):
    """Admin updates and then gets a driver's score."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    score_data = {
        "overall_safety_score": 85.5,
        "efficiency_score": 90,
        "feedback_summary": "Good performance."
    }
    put_response = client.put(f'/api/monitoring/drivers/{registered_driver["id"]}/score', headers=headers, json=score_data)
    assert put_response.status_code == 200
    assert put_response.get_json()['score']['overall_safety_score'] == 85.5

    get_response = client.get(f'/api/monitoring/drivers/{registered_driver["id"]}/score', headers=headers)
    assert get_response.status_code == 200
    json_resp = get_response.get_json()
    assert json_resp['overall_safety_score'] == 85.5
    assert json_resp['efficiency_score'] == 90
    assert json_resp['feedback_summary'] == "Good performance."

def test_update_driver_score_invalid_value(client, registered_admin, registered_driver):
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    score_data = {"overall_safety_score": 101} # Invalid
    response = client.put(f'/api/monitoring/drivers/{registered_driver["id"]}/score', headers=headers, json=score_data)
    assert response.status_code == 400


# --- Test Incident Logging & Reporting Endpoints ---

def test_log_incident_report_by_admin(client, registered_admin, registered_driver):
    """Admin logs an incident report."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    incident_data = {
        "driver_id": registered_driver["id"],
        "incident_type": "minor_accident",
        "description": "Scratched bumper in parking lot.",
        "status": "open"
    }
    response = client.post('/api/monitoring/incidents', headers=headers, json=incident_data)
    assert response.status_code == 201
    json_resp = response.get_json()['report']
    assert json_resp['driver_id'] == registered_driver["id"]
    assert json_resp['incident_type'] == "minor_accident"
    assert json_resp['reported_by_user_id'] == registered_admin["id"]

def test_get_all_incidents_by_admin(client, registered_admin, registered_driver):
    """Admin gets all incidents, with filtering."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    # Log one incident
    client.post('/api/monitoring/incidents', headers=headers, json={
        "driver_id": registered_driver["id"], "incident_type": "complaint",
        "description": "Passenger complaint about music.", "status": "investigating"
    })

    response = client.get('/api/monitoring/incidents', headers=headers)
    assert response.status_code == 200
    assert len(response.get_json()['incidents']) >= 1

    # Test filtering
    response_filtered = client.get(f'/api/monitoring/incidents?driver_id={registered_driver["id"]}&status=investigating', headers=headers)
    assert response_filtered.status_code == 200
    assert len(response_filtered.get_json()['incidents']) == 1
    assert response_filtered.get_json()['incidents'][0]['incident_type'] == "complaint"


def test_get_specific_incident_by_admin(client, registered_admin, registered_driver):
    """Admin gets details of a specific incident."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    post_resp = client.post('/api/monitoring/incidents', headers=headers, json={
        "driver_id": registered_driver["id"], "incident_type": "speed_warning",
        "description": "Exceeded speed by 20 km/h", "status": "open"
    })
    report_id = post_resp.get_json()['report']['report_id']

    response = client.get(f'/api/monitoring/incidents/{report_id}', headers=headers)
    assert response.status_code == 200
    assert response.get_json()['report_id'] == report_id

def test_update_incident_report_by_admin(client, registered_admin, registered_driver):
    """Admin updates an incident report."""
    headers = {'Authorization': f'Bearer {registered_admin["token"]}'}
    post_resp = client.post('/api/monitoring/incidents', headers=headers, json={
        "driver_id": registered_driver["id"], "incident_type": "vehicle_issue",
        "description": "Flat tire reported.", "status": "open"
    })
    report_id = post_resp.get_json()['report']['report_id']

    update_data = {"status": "resolved", "resolution_notes": "Tire replaced by roadside assistance."}
    response = client.put(f'/api/monitoring/incidents/{report_id}', headers=headers, json=update_data)
    assert response.status_code == 200
    json_resp = response.get_json()['report']
    assert json_resp['status'] == "resolved"
    assert json_resp['resolution_notes'] == "Tire replaced by roadside assistance."

def test_incident_access_by_non_admin_fails(client, registered_user, registered_admin, registered_driver): # Added registered_admin to ensure it's available
    """Non-admin attempts to access incident endpoints."""
    # Need an incident created by an admin first
    # Use the admin fixture directly
    admin_headers = {'Authorization': f'Bearer {registered_admin["token"]}'}

    post_resp = client.post('/api/monitoring/incidents', headers=admin_headers, json={
        "driver_id": registered_driver["id"], "incident_type": "test_incident",
        "description": "A test incident.", "status": "open"
    })
    assert post_resp.status_code == 201 # Ensure incident created
    report_id = post_resp.get_json()['report']['report_id']


    user_headers = {'Authorization': f'Bearer {registered_user["token"]}'} # Passenger/non-admin

    response_post = client.post('/api/monitoring/incidents', headers=user_headers, json={
        "driver_id": registered_driver["id"], "incident_type": "another_incident", "description": "..."})
    assert response_post.status_code == 403

    response_get_all = client.get('/api/monitoring/incidents', headers=user_headers)
    assert response_get_all.status_code == 403

    response_get_one = client.get(f'/api/monitoring/incidents/{report_id}', headers=user_headers)
    assert response_get_one.status_code == 403

    response_put = client.put(f'/api/monitoring/incidents/{report_id}', headers=user_headers, json={"status": "closed"})
    assert response_put.status_code == 403
