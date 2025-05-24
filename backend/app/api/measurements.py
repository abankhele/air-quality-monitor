from flask import jsonify, request
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from app.database import db
from app.models import Location, Sensor, Parameter, Measurement
from app.api import api_bp
from app import cache

@api_bp.route('/measurements', methods=['GET'])
@cache.cached(timeout=180, query_string=True)
def get_measurements():
    """Get measurements with filtering options - HARDCODED FROM MAY 21, 2025"""
    sensor_id = request.args.get('sensor_id', type=int)
    location_id = request.args.get('location_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # HARDCODED START DATE - NO MORE 2016/2018 BULLSHIT
    start_date = datetime(2025, 5, 21)  # May 21, 2025
    
    # Build optimized query
    query = db.session.query(Measurement).options(
        joinedload(Measurement.sensor).joinedload(Sensor.parameter),
        joinedload(Measurement.sensor).joinedload(Sensor.location)
    )
    
    # ALWAYS apply the hardcoded date filter
    query = query.filter(Measurement.timestamp >= start_date)
    
    # Apply other filters
    if sensor_id:
        query = query.filter(Measurement.sensor_id == sensor_id)
    elif location_id and parameter_id:
        query = query.join(Sensor).filter(
            Sensor.location_id == location_id,
            Sensor.parameter_id == parameter_id
        )
    elif location_id:
        query = query.join(Sensor).filter(Sensor.location_id == location_id)
    elif parameter_id:
        query = query.join(Sensor).filter(Sensor.parameter_id == parameter_id)
    
    # Order by timestamp descending
    query = query.order_by(Measurement.timestamp.desc())
    
    # Get total count
    total = query.count()
    
    # Apply limit ONLY if specified - NO DEFAULT LIMIT
    if limit:
        measurements = query.limit(limit).offset(offset).all()
    else:
        measurements = query.offset(offset).all()
    
    # Format response
    result = []
    for m in measurements:
        if m.sensor and m.sensor.parameter and m.sensor.location:
            result.append({
                'id': m.id,
                'value': float(m.value),
                'timestamp': m.timestamp.isoformat(),
                'sensor': {
                    'id': m.sensor.id,
                    'openaq_id': m.sensor.openaq_id
                },
                'parameter': {
                    'id': m.sensor.parameter.id,
                    'name': m.sensor.parameter.name,
                    'display_name': m.sensor.parameter.display_name,
                    'unit': m.sensor.parameter.unit
                },
                'location': {
                    'id': m.sensor.location.id,
                    'name': m.sensor.location.name,
                    'latitude': float(m.sensor.location.latitude),
                    'longitude': float(m.sensor.location.longitude)
                }
            })
    
    return jsonify({
        'results': result,
        'meta': {
            'limit': limit if limit else 'no_limit',
            'offset': offset,
            'total': total,
            'found': len(result),
            'start_date': start_date.isoformat(),
            'note': 'Hardcoded to show data from May 21, 2025 onwards only'
        }
    })

@api_bp.route('/measurements/latest', methods=['GET'])
@cache.cached(timeout=300)
def get_latest_measurements():
    """Get latest measurements for all sensors - HARDCODED FROM MAY 21, 2025"""
    # HARDCODED START DATE
    start_date = datetime(2025, 5, 21)
    
    # Get all sensors with valid parameter_id and location_id
    sensors = Sensor.query.options(
        joinedload(Sensor.parameter),
        joinedload(Sensor.location)
    ).filter(
        Sensor.parameter_id.is_not(None),
        Sensor.location_id.is_not(None)
    ).all()
    
    result = []
    for sensor in sensors:
        # Get latest measurement for this sensor AFTER May 21, 2025
        measurement = Measurement.query.filter(
            Measurement.sensor_id == sensor.id,
            Measurement.timestamp >= start_date  # HARDCODED DATE FILTER
        ).order_by(Measurement.timestamp.desc()).first()
        
        if measurement and sensor.parameter and sensor.location:
            result.append({
                'value': float(measurement.value),
                'timestamp': measurement.timestamp.isoformat(),
                'sensor': {
                    'id': sensor.id,
                    'openaq_id': sensor.openaq_id
                },
                'parameter': {
                    'id': sensor.parameter.id,
                    'name': sensor.parameter.name,
                    'display_name': sensor.parameter.display_name,
                    'unit': sensor.parameter.unit
                },
                'location': {
                    'id': sensor.location.id,
                    'name': sensor.location.name,
                    'latitude': float(sensor.location.latitude),
                    'longitude': float(sensor.location.longitude)
                }
            })
    
    return jsonify(result)

@api_bp.route('/measurements/debug', methods=['GET'])
def debug_measurements():
    """Debug endpoint - HARDCODED FROM MAY 21, 2025"""
    try:
        # HARDCODED START DATE
        start_date = datetime(2025, 5, 21)
        
        # Basic counts
        measurement_count = Measurement.query.count()
        fresh_measurement_count = Measurement.query.filter(Measurement.timestamp >= start_date).count()
        sensor_count = Sensor.query.count()
        valid_sensor_count = Sensor.query.filter(
            Sensor.parameter_id.is_not(None),
            Sensor.location_id.is_not(None)
        ).count()
        
        # Recent measurements FROM MAY 21, 2025
        recent_measurements = Measurement.query.filter(
            Measurement.timestamp >= start_date
        ).order_by(Measurement.timestamp.desc()).limit(5).all()
        
        debug_info = {
            'total_measurements': measurement_count,
            'fresh_measurements_since_may_21': fresh_measurement_count,
            'total_sensors': sensor_count,
            'valid_sensors': valid_sensor_count,
            'start_date_filter': start_date.isoformat(),
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
