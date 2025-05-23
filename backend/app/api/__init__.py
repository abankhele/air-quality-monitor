from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes at the end
from app.api import locations, parameters, measurements, stats
