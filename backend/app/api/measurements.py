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
    """Get measurements with filtering options - NO DATE FILTERING - SHOW ALL HISTORICAL DATA"""
    sensor_id = request.args.get('sensor_id', type=int)
    location_id = request.args.get('location_id', type=int)
    parameter_id = request.args.get('parameter_id', type=int)
    days = request.args.get('days', type=int)  # Optional date filtering
    limit = request.args.get('limit', type=int)  # NO DEFAULT LIMIT
    offset = request.args.get('offset', 0, type=int)
    
    # Build optimized query with eager loading
    query = db.session.query(Measurement).options(
        joinedload(Measurement.sensor).joinedload(Sensor.parameter),
        joinedload(Measurement.sensor).joinedload(Sensor.location)
    )
    
    # Apply date filtering ONLY if explicitly requested by user
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Measurement.timestamp >= start_date)
    # NO AUTOMATIC DATE FILTERING - SHOW ALL HISTORICAL DATA
    
    # Apply other filters with optimized joins
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
    
    # Get total count for pagination
    total = query.count()
    
    # Apply limit ONLY if specified - NO DEFAULT LIMIT
    if limit:
        measurements = query.limit(limit).offset(offset).all()
    else:
        # Get ALL measurements if no limit specified
        measurements = query.offset(offset).all()
    
    # Format response (relationships already loaded via eager loading)
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
            'note': 'All historical data available - no date filtering applied'
        }
    })

@api_bp.route('/measurements/latest', methods=['GET'])
@cache.cached(timeout=300)
def get_latest_measurements():
    """Get latest measurements for all sensors - NO DATE FILTERING"""
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
        # Get latest measurement for this sensor - NO DATE FILTERING
        measurement = Measurement.query.filter_by(
            sensor_id=sensor.id
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

@api_bp.route('/measurements/data-range', methods=['GET'])
@cache.cached(timeout=3600)
def get_data_range():
    """Get the date range of available data for each location"""
    location_id = request.args.get('location_id', type=int)
    
    if location_id:
        # Get date range for specific location
        query = db.session.query(
            db.func.min(Measurement.timestamp).label('oldest'),
            db.func.max(Measurement.timestamp).label('newest'),
            db.func.count(Measurement.id).label('total_measurements')
        ).join(Sensor).filter(Sensor.location_id == location_id)
        
        result = query.first()
        
        if result and result.oldest:
            return jsonify({
                'location_id': location_id,
                'oldest_data': result.oldest.isoformat(),
                'newest_data': result.newest.isoformat(),
                'total_measurements': result.total_measurements,
                'data_span_years': (result.newest - result.oldest).days / 365.25 if result.newest and result.oldest else 0
            })
        else:
            return jsonify({
                'location_id': location_id,
                'message': 'No data available for this location'
            })
    else:
        # Get overall data range
        query = db.session.query(
            db.func.min(Measurement.timestamp).label('oldest'),
            db.func.max(Measurement.timestamp).label('newest'),
            db.func.count(Measurement.id).label('total_measurements')
        )
        
        result = query.first()
        
        return jsonify({
            'overall_oldest_data': result.oldest.isoformat() if result.oldest else None,
            'overall_newest_data': result.newest.isoformat() if result.newest else None,
            'total_measurements': result.total_measurements,
            'data_span_years': (result.newest - result.oldest).days / 365.25 if result.newest and result.oldest else 0
        })

@api_bp.route('/measurements/debug', methods=['GET'])
def debug_measurements():
    """Debug endpoint to check measurement data - NO DATE FILTERING"""
    try:
        # Basic counts
        measurement_count = Measurement.query.count()
        sensor_count = Sensor.query.count()
        valid_sensor_count = Sensor.query.filter(
            Sensor.parameter_id.is_not(None),
            Sensor.location_id.is_not(None)
        ).count()
        
        # Recent measurements (last 5)
        recent_measurements = Measurement.query.order_by(Measurement.timestamp.desc()).limit(5).all()
        
        # Oldest measurements (first 5)
        oldest_measurements = Measurement.query.order_by(Measurement.timestamp.asc()).limit(5).all()
        
        # Get date range
        date_range = db.session.query(
            db.func.min(Measurement.timestamp).label('oldest'),
            db.func.max(Measurement.timestamp).label('newest')
        ).first()
        
        debug_info = {
            'total_measurements': measurement_count,
            'total_sensors': sensor_count,
            'valid_sensors': valid_sensor_count,
            'oldest_data': date_range.oldest.isoformat() if date_range.oldest else None,
            'newest_data': date_range.newest.isoformat() if date_range.newest else None,
            'data_span_years': (date_range.newest - date_range.oldest).days / 365.25 if date_range.newest and date_range.oldest else 0,
            'recent_measurements': [],
            'oldest_measurements': []
        }
        
        for m in recent_measurements:
            debug_info['recent_measurements'].append({
                'id': m.id,
                'sensor_id': m.sensor_id,
                'value': float(m.value),
                'timestamp': m.timestamp.isoformat()
            })
        
        for m in oldest_measurements:
            debug_info['oldest_measurements'].append({
                'id': m.id,
                'sensor_id': m.sensor_id,
                'value': float(m.value),
                'timestamp': m.timestamp.isoformat()
            })
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
