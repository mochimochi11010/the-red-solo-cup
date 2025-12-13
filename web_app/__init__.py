import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Set secret key for session management (required for flash messages)
    app.secret_key = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    from .routes.home_routes import home_routes
    app.register_blueprint(home_routes)

    return app
