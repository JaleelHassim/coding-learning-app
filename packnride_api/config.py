import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file (if it exists)

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_default_jwt_secret_key')
    # Add other configurations here
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # Example: Use an in-memory SQLite database for tests if we add a DB
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration."""
    # Production specific settings
    # For example, load sensitive keys from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not SECRET_KEY or not JWT_SECRET_KEY:
        # In a real production environment, you'd want to ensure these are set
        # and potentially raise an error or log a critical warning.
        # For now, we'll just print a warning if they're not found.
        print("WARNING: SECRET_KEY or JWT_SECRET_KEY not set in environment for ProductionConfig.")
        if not SECRET_KEY:
            SECRET_KEY = 'prod_default_secret_key_fallback' # Fallback for safety, but not recommended
        if not JWT_SECRET_KEY:
            JWT_SECRET_KEY = 'prod_default_jwt_secret_key_fallback' # Fallback for safety

# Simple way to get the config based on an environment variable
# You might set FLASK_ENV to 'development', 'testing', or 'production'
env_config = os.environ.get('FLASK_ENV', 'development').lower()

if env_config == 'production':
    app_config = ProductionConfig()
elif env_config == 'testing':
    app_config = TestingConfig()
else:
    app_config = DevelopmentConfig()
