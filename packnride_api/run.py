from app import create_app
from config import app_config

app = create_app(app_config)

if __name__ == '__main__':
    # Ensure FLASK_ENV is set, or default to development for running directly
    # The app_config loaded by create_app already considers FLASK_ENV
    host = '0.0.0.0'
    port = 5000 # Standard Flask port
    print(f"Starting PacknRide API on {host}:{port} with config: {app.config['ENV']}")
    app.run(host=host, port=port, debug=app.config['DEBUG'])
