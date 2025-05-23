from flask import jsonify
from app.models import Parameter
from app.api import api_bp

@api_bp.route('/parameters', methods=['GET'])
def get_parameters():
    """Get all available parameters"""
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
def get_parameter(parameter_id):
    """Get details for a specific parameter"""
    parameter = Parameter.query.get_or_404(parameter_id)
    
    result = {
        'id': parameter.id,
        'name': parameter.name,
        'display_name': parameter.display_name,
        'unit': parameter.unit
    }
    
    return jsonify(result)
