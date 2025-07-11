from flask import Flask
from flask_jwt_extended import JWTManager
from ..config import app_config

# In-memory 'database' for simplicity
users_db = {}
rides_db = {}
driving_events_db = {}
driver_scores_db = {}
incident_reports_db = {}

class IDManager:
    def __init__(self):
        self.user_id_counter = 0
        self.ride_id_counter = 0
        self.driving_event_id_counter = 0
        self.incident_report_id_counter = 0

    def get_next_user_id(self):
        self.user_id_counter += 1
        return self.user_id_counter

    def get_next_ride_id(self):
        self.ride_id_counter += 1
        return self.ride_id_counter

    def get_next_driving_event_id(self):
        self.driving_event_id_counter += 1
        return self.driving_event_id_counter

    def get_next_incident_report_id(self):
        self.incident_report_id_counter += 1
        return self.incident_report_id_counter

id_manager = IDManager()
jwt = JWTManager()

def create_app(config_object=app_config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    jwt.init_app(app)

    from .auth import auth_bp
    from .routes import main_bp
    from .monitoring_routes import monitoring_bp # Import new blueprint

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring') # Register it

    @app.route('/health')
    def health_check():
        return "PacknRide API is healthy!", 200

    @jwt.user_identity_loader
    def user_identity_lookup(user_identity_dict):
        return user_identity_dict

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user_email = identity.get("email")
        is_admin_claim = False
        if user_email and user_email in users_db:
            user = users_db[user_email]
            is_admin_claim = user.get("is_admin", False)
        return {"is_admin": is_admin_claim}

    return app
