from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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

def create_celery(app):
    """Create Celery instance"""
    from backend.celery_app import make_celery
    celery = make_celery(app.import_name)
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
