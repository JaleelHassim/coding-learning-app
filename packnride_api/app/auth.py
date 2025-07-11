from flask import Blueprint, request, jsonify
from app import users_db
from app.utils import hash_password, verify_password
from flask_jwt_extended import create_access_token
import datetime
from app import id_manager


auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type', 'passenger')
    is_admin = data.get('is_admin', False) # New field, defaults to False

    if not email or not password or not name:
        return jsonify({"error": "Missing name, email, or password"}), 400

    if user_type not in ['passenger', 'driver']:
        return jsonify({"error": "Invalid user_type. Must be 'passenger' or 'driver'"}), 400

    if not isinstance(is_admin, bool):
        return jsonify({"error": "Invalid is_admin flag. Must be true or false."}), 400

    if email in users_db:
        return jsonify({"error": "Email already registered"}), 409

    current_id = id_manager.get_next_user_id()
    hashed_pass = hash_password(password)

    user_obj = {
        "id": current_id,
        "name": name,
        "email": email,
        "password_hash": hashed_pass,
        "user_type": user_type,
        "is_admin": is_admin, # Store is_admin status
        "registered_on": datetime.datetime.utcnow().isoformat()
    }
    users_db[email] = user_obj

    return jsonify({
        "message": "User registered successfully",
        "user": {"id": user_obj["id"], "name": name, "email": email, "user_type": user_type, "is_admin": is_admin}
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = users_db.get(email)
    if not user:
        return jsonify({"error": "Email not found"}), 404

    if not verify_password(password, user['password_hash']):
        return jsonify({"error": "Invalid credentials"}), 401

    # Include is_admin in the identity for the token
    identity_data = {
        "id": user["id"],
        "email": user["email"],
        "user_type": user["user_type"],
        "is_admin": user.get("is_admin", False) # Get is_admin status
    }
    access_token = create_access_token(identity=identity_data)
    return jsonify(access_token=access_token), 200
