from flask import jsonify
from app.database import db
from app.models import Parameter
from app.api import api_bp
from app import cache

@api_bp.route('/parameters', methods=['GET'])
@cache.cached(timeout=3600)  # Cache for 1 hour (parameters rarely change)
def get_parameters():
    """Get all parameters (with caching added)"""
    parameters = Parameter.query.all()
    
    result = []
    for param in parameters:
        result.append({
            'id': param.id,
            'name': param.name,
            'display_name': param.display_name,
            'unit': param.unit
        })
    
    return jsonify(result)

@api_bp.route('/parameters/<int:parameter_id>', methods=['GET'])
@cache.cached(timeout=3600)  # Cache for 1 hour
def get_parameter(parameter_id):
    """Get details for a specific parameter (with caching added)"""
    parameter = Parameter.query.get_or_404(parameter_id)
    
    result = {
        'id': parameter.id,
        'name': parameter.name,
        'display_name': parameter.display_name,
        'unit': parameter.unit
    }
    
    return jsonify(result)
