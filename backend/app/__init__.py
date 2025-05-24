from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_caching import Cache
from config import Config
from app.database import db

cache = Cache()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Add cache configuration
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/1'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
    
    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    CORS(app)
    
    # Import models to register them
    from app import models
    
    # Register API blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp)
    
    return app

def create_celery(app):
    """Create Celery instance with Flask app context"""
    from celery_app import make_celery
    celery = make_celery()
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
