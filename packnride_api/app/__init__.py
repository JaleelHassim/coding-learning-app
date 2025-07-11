from flask import Flask
from flask_jwt_extended import JWTManager
from ..config import app_config

# In-memory 'database' for simplicity
users_db = {}  # Store user data: {email: user_object}
rides_db = {}  # Store ride data: {ride_id: ride_object}

# Class to manage ID generation for in-memory store
class IDManager:
    def __init__(self):
        self.user_id_counter = 0
        self.ride_id_counter = 0

    def get_next_user_id(self):
        self.user_id_counter += 1
        return self.user_id_counter

    def get_next_ride_id(self):
        self.ride_id_counter += 1
        return self.ride_id_counter

id_manager = IDManager()

jwt = JWTManager()

def create_app(config_object=app_config):
    """
    Application factory pattern: creates and configures the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialize extensions
    jwt.init_app(app)

    # Register Blueprints
    from .auth import auth_bp
    from .routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/api')

    @app.route('/health')
    def health_check():
        return "PacknRide API is healthy!", 200

    # Callback for defining user identity from JWT
    @jwt.user_identity_loader
    def user_identity_lookup(user_identity):
        return user_identity # The identity is already a dict from create_access_token

    # Optional: Callback for loading user object from identity (if needed by @jwt_required)
    # For simple cases where identity is enough, this isn't strictly necessary
    # but good practice if you need to load the full user object often.
    # @jwt.user_lookup_loader
    # def user_lookup_callback(_jwt_header, jwt_data):
    #     identity = jwt_data["sub"] # 'sub' is the key for identity in jwt_data
    #     user_email = identity.get("email")
    #     if user_email and user_email in users_db:
    #         return users_db[user_email]
    #     return None


    return app
