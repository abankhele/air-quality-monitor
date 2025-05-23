from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Import and register blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp)
    
    # Import models and API routes AFTER everything is set up
    with app.app_context():
        from app import models
        from app.api import register_routes
        register_routes()
    
    return app
