from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

def register_routes():
    from app.api import locations, parameters, measurements, stats
