from flask import jsonify, request
from datetime import datetime, timedelta
from app.models import db, Measurement, Sensor, Parameter, Location
from app.api import api_bp

@api_bp.route('/measurements', methods=['GET'])
def get_measurements():
    """Get measurements with filtering options"""
    # Parse query parameters
    sensor_id = request.args.get('sensor_id', type=int)
    location_id = request.args.get('location_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    days = request.args.get('days', 1, type=int)
    limit = request.args.get('limit', 1000, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build query
    query = Measurement.query.filter(Measurement.timestamp >= start_date)
    
    # Apply filters
    if sensor_id:
        query = query.filter(Measurement.sensor_id == sensor_id)
    elif location_id and parameter_id:
        # Find sensors at this location for this parameter
        sensors = Sensor.query.filter_by(location_id=location_id, parameter_id=parameter_id).all()
        sensor_ids = [s.id for s in sensors]
        if sensor_ids:
            query = query.filter(Measurement.sensor_id.in_(sensor_ids))
        else:
            return jsonify({'results': [], 'meta': {'total': 0}})
    elif location_id:
        # Find all sensors at this location
        sensors = Sensor.query.filter_by(location_id=location_id).all()
        sensor_ids = [s.id for s in sensors]
        if sensor_ids:
            query = query.filter(Measurement.sensor_id.in_(sensor_ids))
        else:
            return jsonify({'results': [], 'meta': {'total': 0}})
    elif parameter_id:
        # Find all sensors for this parameter
        sensors = Sensor.query.filter_by(parameter_id=parameter_id).all()
        sensor_ids = [s.id for s in sensors]
        if sensor_ids:
            query = query.filter(Measurement.sensor_id.in_(sensor_ids))
        else:
            return jsonify({'results': [], 'meta': {'total': 0}})
    
    # Order by timestamp descending (newest first)
    query = query.order_by(Measurement.timestamp.desc())
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    measurements = query.limit(limit).offset(offset).all()
    
    # Format response
    result = []
    for m in measurements:
        sensor = Sensor.query.get(m.sensor_id)
        parameter = Parameter.query.get(sensor.parameter_id)
        location = Location.query.get(sensor.location_id)
        
        result.append({
            'id': m.id,
            'value': float(m.value),
            'timestamp': m.timestamp.isoformat(),
            'sensor': {
                'id': sensor.id,
                'openaq_id': sensor.openaq_id
            },
            'parameter': {
                'id': parameter.id,
                'name': parameter.name,
                'display_name': parameter.display_name,
                'unit': parameter.unit
            },
            'location': {
                'id': location.id,
                'name': location.name,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude)
            }
        })
    
    return jsonify({
        'results': result,
        'meta': {
            'limit': limit,
            'offset': offset,
            'total': total,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    })

@api_bp.route('/measurements/latest', methods=['GET'])
def get_latest_measurements():
    """Get latest measurements for all sensors"""
    # Get all sensors
    sensors = Sensor.query.all()
    
    result = []
    for sensor in sensors:
        # Get latest measurement for this sensor
        measurement = Measurement.query.filter_by(sensor_id=sensor.id).order_by(Measurement.timestamp.desc()).first()
        
        if measurement:
            parameter = Parameter.query.get(sensor.parameter_id)
            location = Location.query.get(sensor.location_id)
            
            result.append({
                'value': float(measurement.value),
                'timestamp': measurement.timestamp.isoformat(),
                'sensor': {
                    'id': sensor.id,
                    'openaq_id': sensor.openaq_id
                },
                'parameter': {
                    'id': parameter.id,
                    'name': parameter.name,
                    'display_name': parameter.display_name,
                    'unit': parameter.unit
                },
                'location': {
                    'id': location.id,
                    'name': location.name,
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude)
                }
            })
    
    return jsonify(result)
