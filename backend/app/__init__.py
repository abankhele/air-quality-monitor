from flask import Flask
from flask_cors import CORS
from config import Config
from app.database import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Import models to register them
    from app import models
    
    # Register API blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp)
    
    return app
