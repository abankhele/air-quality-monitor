from flask import jsonify, request
from datetime import datetime, timedelta
from app.database import db
from app.models import Location, Sensor, Parameter, Measurement
from app.api import api_bp

@api_bp.route('/measurements', methods=['GET'])
def get_measurements():
    """Get measurements with filtering options"""
    # Parse query parameters
    sensor_id = request.args.get('sensor_id', type=int)
    location_id = request.args.get('location_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    days = request.args.get('days', type=int)  # Make days optional
    limit = request.args.get('limit', None, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build base query
    query = Measurement.query
    
    # Apply date filtering only if days parameter is provided
    if days:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        query = query.filter(Measurement.timestamp >= start_date)
    
    # Apply filters
    if sensor_id:
        query = query.filter(Measurement.sensor_id == sensor_id)
    elif location_id and parameter_id:
        # Find sensors at this location for this parameter
        sensors = Sensor.query.filter_by(location_id=location_id, parameter_id=parameter_id).filter(Sensor.parameter_id.is_not(None)).all()
        sensor_ids = [s.id for s in sensors]
        if sensor_ids:
            query = query.filter(Measurement.sensor_id.in_(sensor_ids))
        else:
            return jsonify({'results': [], 'meta': {'total': 0}})
    elif location_id:
        # Find all sensors at this location
        sensors = Sensor.query.filter_by(location_id=location_id).filter(Sensor.parameter_id.is_not(None)).all()
        sensor_ids = [s.id for s in sensors]
        if sensor_ids:
            query = query.filter(Measurement.sensor_id.in_(sensor_ids))
        else:
            return jsonify({'results': [], 'meta': {'total': 0}})
    elif parameter_id:
        # Find all sensors for this parameter
        sensors = Sensor.query.filter_by(parameter_id=parameter_id).filter(Sensor.parameter_id.is_not(None)).all()
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
        if not sensor or not sensor.parameter_id or not sensor.location_id:
            continue
            
        parameter = Parameter.query.get(sensor.parameter_id)
        location = Location.query.get(sensor.location_id)
        
        if not parameter or not location:
            continue
        
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
    
    # Build meta response
    meta = {
        'limit': limit,
        'offset': offset,
        'total': total,
        'found': len(result)
    }
    
    if days:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        meta['start_date'] = start_date.isoformat()
        meta['end_date'] = end_date.isoformat()
    else:
        meta['note'] = 'No date filtering applied'
    
    return jsonify({
        'results': result,
        'meta': meta
    })

@api_bp.route('/measurements/latest', methods=['GET'])
def get_latest_measurements():
    """Get latest measurements for all sensors"""
    # Get all sensors with valid parameter_id and location_id
    sensors = Sensor.query.filter(
        Sensor.parameter_id.is_not(None),
        Sensor.location_id.is_not(None)
    ).all()
    
    result = []
    for sensor in sensors:
        # Get latest measurement for this sensor
        measurement = Measurement.query.filter_by(sensor_id=sensor.id).order_by(Measurement.timestamp.desc()).first()
        
        if measurement:
            parameter = Parameter.query.get(sensor.parameter_id)
            location = Location.query.get(sensor.location_id)
            
            if parameter and location:  # Only include if both exist
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

@api_bp.route('/measurements/debug', methods=['GET'])
def debug_measurements():
    """Debug endpoint to check measurement data"""
    try:
        # Basic counts
        measurement_count = Measurement.query.count()
        sensor_count = Sensor.query.count()
        valid_sensor_count = Sensor.query.filter(
            Sensor.parameter_id.is_not(None),
            Sensor.location_id.is_not(None)
        ).count()
        
        # Recent measurements
        recent_measurements = Measurement.query.order_by(Measurement.timestamp.desc()).limit(5).all()
        
        # Check for measurements in the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_count = Measurement.query.filter(Measurement.timestamp >= thirty_days_ago).count()
        
        debug_info = {
            'total_measurements': measurement_count,
            'total_sensors': sensor_count,
            'valid_sensors': valid_sensor_count,
            'measurements_last_30_days': recent_count,
            'recent_measurements': []
        }
        
        for m in recent_measurements:
            debug_info['recent_measurements'].append({
                'id': m.id,
                'sensor_id': m.sensor_id,
                'value': float(m.value),
                'timestamp': m.timestamp.isoformat()
            })
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/measurements/test-simple', methods=['GET'])
def test_simple_measurements():
    """Simple test to get any measurements"""
    try:
        # Get any 10 measurements without date filtering
        measurements = Measurement.query.limit(10).all()
        
        result = []
        for m in measurements:
            result.append({
                'id': m.id,
                'sensor_id': m.sensor_id,
                'value': float(m.value),
                'timestamp': m.timestamp.isoformat()
            })
        
        return jsonify({
            'count': len(result),
            'measurements': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
