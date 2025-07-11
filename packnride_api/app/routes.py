from flask import Blueprint, jsonify, request
from app import rides_db, users_db, id_manager # Import DBs and ID manager
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
import random # For mock fare estimation

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to PacknRide API - Main Routes"}), 200

# --- Ride Endpoints ---

@main_bp.route('/rides/request', methods=['POST'])
@jwt_required()
def request_ride():
    current_user_identity = get_jwt_identity() # This is the dict we stored
    passenger_id = current_user_identity.get('id')
    user_type = current_user_identity.get('user_type')

    if user_type != 'passenger':
        return jsonify({"error": "Only passengers can request rides"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    pickup_location = data.get('pickup_location')
    dropoff_location = data.get('dropoff_location')

    if not pickup_location or not dropoff_location:
        return jsonify({"error": "Missing pickup_location or dropoff_location"}), 400

    ride_id = id_manager.get_next_ride_id()

    ride_obj = {
        "id": ride_id,
        "passenger_id": passenger_id,
        "driver_id": None,
        "pickup_location": pickup_location,
        "dropoff_location": dropoff_location,
        "status": "pending", # pending, accepted, en_route_pickup, arrived_pickup, started, completed, cancelled
        "fare": None,
        "requested_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat()
    }
    rides_db[ride_id] = ride_obj

    return jsonify({"message": "Ride requested successfully", "ride": ride_obj}), 201


@main_bp.route('/rides/<int:ride_id>', methods=['GET'])
@jwt_required()
def get_ride_details(ride_id):
    current_user_identity = get_jwt_identity()
    user_id = current_user_identity.get('id')
    # user_type = current_user_identity.get('user_type') # Not strictly needed here but good for clarity

    ride = rides_db.get(ride_id)
    if not ride:
        return jsonify({"error": "Ride not found"}), 404

    # Allow passenger who requested or assigned driver to see details
    if not (ride['passenger_id'] == user_id or (ride['driver_id'] and ride['driver_id'] == user_id)):
        return jsonify({"error": "Access forbidden: You are not part of this ride"}), 403

    return jsonify(ride), 200


@main_bp.route('/rides/<int:ride_id>/accept', methods=['POST'])
@jwt_required()
def accept_ride(ride_id):
    current_user_identity = get_jwt_identity()
    driver_id = current_user_identity.get('id')
    user_type = current_user_identity.get('user_type')

    if user_type != 'driver':
        return jsonify({"error": "Only drivers can accept rides"}), 403

    ride = rides_db.get(ride_id)
    if not ride:
        return jsonify({"error": "Ride not found"}), 404

    if ride['status'] != 'pending':
        return jsonify({"error": f"Ride cannot be accepted, current status: {ride['status']}"}), 400

    if ride['driver_id'] is not None: # Check if another driver already accepted it
        return jsonify({"error": "Ride already accepted by another driver"}), 409 # Conflict

    ride['driver_id'] = driver_id
    ride['status'] = 'accepted'
    ride['updated_at'] = datetime.datetime.utcnow().isoformat()

    rides_db[ride_id] = ride # Update the ride in our 'DB'

    return jsonify({"message": "Ride accepted successfully", "ride": ride}), 200


@main_bp.route('/rides/<int:ride_id>/status', methods=['PUT'])
@jwt_required()
def update_ride_status(ride_id):
    current_user_identity = get_jwt_identity()
    user_id = current_user_identity.get('id')
    user_type = current_user_identity.get('user_type')

    ride = rides_db.get(ride_id)
    if not ride:
        return jsonify({"error": "Ride not found"}), 404

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Missing 'status' in request body"}), 400

    new_status = data['status']

    # Define valid statuses and transitions (simplified)
    valid_statuses = ['en_route_pickup', 'arrived_pickup', 'started', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status: {new_status}"}), 400

    # Permissions for status updates (simplified)
    can_update = False
    if user_type == 'driver' and ride['driver_id'] == user_id:
        if ride['status'] == 'accepted' and new_status == 'en_route_pickup': can_update = True
        elif ride['status'] == 'en_route_pickup' and new_status == 'arrived_pickup': can_update = True
        elif ride['status'] == 'arrived_pickup' and new_status == 'started': can_update = True
        elif ride['status'] == 'started' and new_status == 'completed':
            can_update = True
            # Mock fare calculation on completion
            ride['fare'] = round(random.uniform(5.0, 50.0) * 100) / 100 # Mock fare e.g., R25.50
        elif new_status == 'cancelled': # Driver can cancel before pickup, or if passenger no-show
            if ride['status'] in ['accepted', 'en_route_pickup', 'arrived_pickup']: can_update = True
    elif user_type == 'passenger' and ride['passenger_id'] == user_id:
        if new_status == 'cancelled': # Passenger can cancel
            if ride['status'] in ['pending', 'accepted', 'en_route_pickup']: can_update = True # Can cancel before driver starts trip

    if not can_update:
         return jsonify({"error": f"Cannot transition from '{ride['status']}' to '{new_status}' or not authorized"}), 403

    ride['status'] = new_status
    ride['updated_at'] = datetime.datetime.utcnow().isoformat()
    rides_db[ride_id] = ride

    return jsonify({"message": f"Ride status updated to {new_status}", "ride": ride}), 200


# --- Driver Endpoints ---

@main_bp.route('/drivers/nearby', methods=['GET'])
@jwt_required() # Passenger needs to be logged in to see nearby drivers
def get_nearby_drivers():
    # This is a MOCKED endpoint. In a real app, this would involve geospatial queries.
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('user_type') != 'passenger':
         return jsonify({"error": "Only passengers can search for nearby drivers"}), 403

    # Mocking: Return a list of all 'driver' type users who are not currently on an active ride
    available_drivers = []
    for _email, user in users_db.items(): # Iterate through users_db which is keyed by email
        if user['user_type'] == 'driver':
            is_on_active_ride = False
            for _ride_id, ride_data in rides_db.items(): # Iterate through rides_db
                if ride_data['driver_id'] == user['id'] and ride_data['status'] not in ['completed', 'cancelled']:
                    is_on_active_ride = True
                    break
            if not is_on_active_ride:
                available_drivers.append({
                    "id": user['id'],
                    "name": user['name'],
                    "mock_location": f"Nearby Location {random.randint(1, 100)}",
                    "vehicle_type": "Sedan", # Mocked
                    "current_status": "available" # Mocked
                })

    return jsonify({"available_drivers": available_drivers}), 200

# --- Fare Estimation ---
@main_bp.route('/rides/estimate_fare', methods=['POST'])
@jwt_required()
def estimate_fare():
    # MOCKED endpoint
    data = request.get_json()
    if not data or not data.get('pickup_location') or not data.get('dropoff_location'):
        return jsonify({"error": "pickup_location and dropoff_location required"}), 400

    pickup = data.get('pickup_location', "")
    dropoff = data.get('dropoff_location', "")

    # Very simple mock: longer names = higher price, plus some randomness
    base_fare = 10.0
    distance_factor = (len(pickup) + len(dropoff)) * 0.1 # Arbitrary calculation
    random_surge = random.uniform(0.8, 1.5)
    estimated_fare = round((base_fare + distance_factor) * random_surge * 100) / 100 # e.g. RXX.XX

    return jsonify({
        "pickup_location": pickup,
        "dropoff_location": dropoff,
        "estimated_fare_rand": f"R{estimated_fare:.2f}", # South African Rand
        "currency": "ZAR",
        "note": "This is a mock estimation. Actual fare may vary."
    }), 200
