from flask import Blueprint, request, jsonify
from app import driving_events_db, users_db, id_manager, driver_scores_db, incident_reports_db # Added incident_reports_db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import datetime

monitoring_bp = Blueprint('monitoring_bp', __name__)

# Helper function to check for admin privileges from JWT
def is_admin_user():
    claims = get_jwt()
    return claims.get("is_admin", False)

# --- Driving Event Endpoints ---
@monitoring_bp.route('/events', methods=['POST'])
@jwt_required()
def log_driving_event():
    current_user_identity = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    required_fields = ['driver_id', 'event_type', 'timestamp', 'location_lat', 'location_lon']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    driver_id = data.get('driver_id')
    event_type = data.get('event_type')
    ride_id = data.get('ride_id')
    details = data.get('details', {})

    target_driver_exists = any(u['id'] == driver_id and u['user_type'] == 'driver' for u in users_db.values())
    if not target_driver_exists:
        return jsonify({"error": f"Driver with id {driver_id} not found."}), 404

    is_current_user_the_driver = (current_user_identity.get('user_type') == 'driver' and
                                  current_user_identity.get('id') == driver_id)

    if not is_admin_user() and not is_current_user_the_driver:
        return jsonify({"error": "Unauthorized to log event for this driver."}), 403

    event_id = id_manager.get_next_driving_event_id()
    event_obj = {
        "event_id": event_id, "driver_id": driver_id, "ride_id": ride_id,
        "event_type": event_type, "timestamp": data.get('timestamp'),
        "location_lat": data.get('location_lat'), "location_lon": data.get('location_lon'),
        "details": details, "logged_at": datetime.datetime.utcnow().isoformat()
    }
    driving_events_db[event_id] = event_obj
    return jsonify({"message": "Driving event logged successfully", "event": event_obj}), 201


@monitoring_bp.route('/drivers/<int:driver_id>/events', methods=['GET'])
@jwt_required()
def get_driver_events(driver_id):
    current_user_identity = get_jwt_identity()
    is_current_user_the_driver = (current_user_identity.get('user_type') == 'driver' and
                                  current_user_identity.get('id') == driver_id)

    if not is_admin_user() and not is_current_user_the_driver:
        return jsonify({"error": "Unauthorized. Admin access or viewing own data required."}), 403

    target_driver_exists = any(u['id'] == driver_id and u['user_type'] == 'driver' for u in users_db.values())
    if not target_driver_exists:
        return jsonify({"error": f"Driver with id {driver_id} not found."}), 404

    event_type_filter = request.args.get('event_type')
    driver_events = []
    for _event_id, event in driving_events_db.items(): # Corrected variable name
        if event['driver_id'] == driver_id:
            if event_type_filter and event['event_type'] != event_type_filter:
                continue
            driver_events.append(event)

    driver_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify({"driver_id": driver_id, "events": driver_events}), 200

# --- Driver Performance Score Endpoints ---
@monitoring_bp.route('/drivers/<int:driver_id>/score', methods=['GET'])
@jwt_required()
def get_driver_score(driver_id):
    current_user_identity = get_jwt_identity()
    is_current_user_the_driver = (current_user_identity.get('user_type') == 'driver' and
                                  current_user_identity.get('id') == driver_id)

    if not is_admin_user() and not is_current_user_the_driver:
        return jsonify({"error": "Unauthorized. Admin access or viewing own score required."}), 403

    target_driver_exists = any(u['id'] == driver_id and u['user_type'] == 'driver' for u in users_db.values())
    if not target_driver_exists:
        return jsonify({"error": f"Driver with id {driver_id} not found."}), 404

    score = driver_scores_db.get(driver_id)
    if not score:
        return jsonify({
            "driver_id": driver_id, "overall_safety_score": None, "efficiency_score": None,
            "punctuality_score": None, "feedback_summary": "No score data available yet.",
            "last_updated_timestamp": None
        }), 200

    return jsonify(score), 200


@monitoring_bp.route('/drivers/<int:driver_id>/score', methods=['PUT'])
@jwt_required()
def update_driver_score(driver_id):
    if not is_admin_user():
        return jsonify({"error": "Unauthorized. Admin access required to update scores."}), 403

    target_driver_exists = any(u['id'] == driver_id and u['user_type'] == 'driver' for u in users_db.values())
    if not target_driver_exists:
        return jsonify({"error": f"Driver with id {driver_id} not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    current_score = driver_scores_db.get(driver_id, {})
    updated_fields = False

    if 'overall_safety_score' in data:
        score_val = data['overall_safety_score']
        if not (isinstance(score_val, (int, float)) and 0 <= score_val <= 100):
            return jsonify({"error": "Invalid overall_safety_score. Must be a number between 0 and 100."}), 400
        current_score['overall_safety_score'] = score_val
        updated_fields = True

    if 'efficiency_score' in data:
        score_val = data['efficiency_score']
        if not (isinstance(score_val, (int, float)) and 0 <= score_val <= 100):
            return jsonify({"error": "Invalid efficiency_score. Must be a number between 0 and 100."}), 400
        current_score['efficiency_score'] = score_val
        updated_fields = True

    if 'punctuality_score' in data:
        score_val = data['punctuality_score']
        if not (isinstance(score_val, (int, float)) and 0 <= score_val <= 100):
            return jsonify({"error": "Invalid punctuality_score. Must be a number between 0 and 100."}), 400
        current_score['punctuality_score'] = score_val
        updated_fields = True

    if 'feedback_summary' in data:
        summary = data['feedback_summary']
        if not isinstance(summary, str):
            return jsonify({"error": "Invalid feedback_summary. Must be a string."}), 400
        current_score['feedback_summary'] = summary
        updated_fields = True

    if not updated_fields and not driver_scores_db.get(driver_id):
         return jsonify({"error": "No valid score fields provided for update."}), 400

    current_score['driver_id'] = driver_id
    current_score['last_updated_timestamp'] = datetime.datetime.utcnow().isoformat()

    driver_scores_db[driver_id] = current_score
    return jsonify({"message": "Driver score updated successfully", "score": current_score}), 200

# --- Incident Logging & Reporting Endpoints ---

@monitoring_bp.route('/incidents', methods=['POST'])
@jwt_required()
def log_incident_report():
    if not is_admin_user():
        return jsonify({"error": "Unauthorized. Admin access required to log incidents."}), 403

    current_user_identity = get_jwt_identity()
    reporter_id = current_user_identity.get('id')

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    required_fields = ['driver_id', 'incident_type', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    driver_id = data.get('driver_id')
    incident_type = data.get('incident_type')
    description = data.get('description')
    ride_id = data.get('ride_id')
    status = data.get('status', 'open')

    target_driver_exists = any(u['id'] == driver_id and u['user_type'] == 'driver' for u in users_db.values())
    if not target_driver_exists:
        return jsonify({"error": f"Driver with id {driver_id} not found."}), 404

    valid_statuses = ['open', 'investigating', 'resolved', 'closed']
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    report_id = id_manager.get_next_incident_report_id()
    report_obj = {
        "report_id": report_id, "driver_id": driver_id, "ride_id": ride_id,
        "reported_by_user_id": reporter_id, "incident_type": incident_type,
        "description": description, "status": status,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
        "resolution_notes": None
    }
    incident_reports_db[report_id] = report_obj
    return jsonify({"message": "Incident reported successfully", "report": report_obj}), 201


@monitoring_bp.route('/incidents', methods=['GET'])
@jwt_required()
def get_all_incidents():
    if not is_admin_user():
        return jsonify({"error": "Unauthorized. Admin access required."}), 403

    filter_driver_id = request.args.get('driver_id', type=int)
    filter_status = request.args.get('status')

    all_incidents = list(incident_reports_db.values())

    if filter_driver_id is not None:
        all_incidents = [report for report in all_incidents if report['driver_id'] == filter_driver_id]

    if filter_status:
        all_incidents = [report for report in all_incidents if report['status'] == filter_status]

    all_incidents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({"incidents": all_incidents}), 200


@monitoring_bp.route('/incidents/<int:report_id>', methods=['GET'])
@jwt_required()
def get_incident_report_details(report_id):
    if not is_admin_user():
        return jsonify({"error": "Unauthorized. Admin access required."}), 403

    report = incident_reports_db.get(report_id)
    if not report:
        return jsonify({"error": f"Incident report with id {report_id} not found."}), 404
    return jsonify(report), 200


@monitoring_bp.route('/incidents/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_incident_report(report_id):
    if not is_admin_user():
        return jsonify({"error": "Unauthorized. Admin access required to update incidents."}), 403

    report = incident_reports_db.get(report_id)
    if not report:
        return jsonify({"error": f"Incident report with id {report_id} not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    updated_fields = False
    if 'status' in data:
        new_status = data['status']
        valid_statuses = ['open', 'investigating', 'resolved', 'closed']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        report['status'] = new_status
        updated_fields = True

    if 'description' in data:
        report['description'] = str(data['description'])
        updated_fields = True

    if 'resolution_notes' in data:
        report['resolution_notes'] = str(data['resolution_notes']) if data['resolution_notes'] is not None else None
        updated_fields = True

    if not updated_fields:
        return jsonify({"error": "No valid fields provided for update."}), 400

    report['updated_at'] = datetime.datetime.utcnow().isoformat()
    incident_reports_db[report_id] = report
    return jsonify({"message": "Incident report updated successfully", "report": report}), 200
