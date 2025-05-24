from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
from app.database import db
from app.models import Location, Sensor, Parameter, Measurement
from app.api import api_bp
from app.api.utils import parse_bounds
from app import cache

@api_bp.route('/locations', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes
def get_locations():
    """Get all locations with optimized queries"""
    # Parse query parameters
    bounds = parse_bounds(request)
    limit = request.args.get('limit', 1000, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Optimized query with eager loading - eliminates N+1 queries
    query = db.session.query(Location).options(
        selectinload(Location.sensors).joinedload(Sensor.parameter)
    )
    
    # Apply geographic bounds if provided
    if bounds:
        query = query.filter(
            Location.latitude >= bounds['south'],
            Location.latitude <= bounds['north'],
            Location.longitude >= bounds['west'],
            Location.longitude <= bounds['east']
        )
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    locations = query.limit(limit).offset(offset).all()
    
    # Format response (sensors and parameters already loaded via eager loading)
    result = []
    for loc in locations:
        sensor_data = []
        
        # Process sensors (already loaded, no additional queries)
        for sensor in loc.sensors:
            if sensor.parameter:  # Already loaded via joinedload
                sensor_data.append({
                    'id': sensor.id,
                    'openaq_id': sensor.openaq_id,
                    'parameter': {
                        'id': sensor.parameter.id,
                        'name': sensor.parameter.name,
                        'display_name': sensor.parameter.display_name,
                        'unit': sensor.parameter.unit
                    },
                    'last_value': float(sensor.last_value) if sensor.last_value else None,
                    'last_updated': sensor.last_updated.isoformat() if sensor.last_updated else None
                })
        
        # Calculate simple AQI (preserved from original)
        pm25_sensor = next((s for s in sensor_data if s['parameter']['name'] == 'pm25'), None)
        aqi = calculate_aqi_from_pm25(pm25_sensor['last_value']) if pm25_sensor and pm25_sensor['last_value'] else None
        
        result.append({
            'id': loc.id,
            'openaq_id': loc.openaq_id,
            'name': loc.name,
            'locality': loc.locality,
            'country_code': loc.country_code,
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
            'is_mobile': loc.is_mobile,
            'last_updated': loc.last_updated.isoformat() if loc.last_updated else None,
            'sensors': sensor_data,
            'aqi': aqi
        })
    
    return jsonify({
        'results': result,
        'meta': {
            'limit': limit,
            'offset': offset,
            'total': total
        }
    })

@api_bp.route('/locations/<int:location_id>', methods=['GET'])
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_location(location_id):
    """Get details for a specific location with optimized query"""
    # Optimized query with eager loading
    location = db.session.query(Location).options(
        selectinload(Location.sensors).joinedload(Sensor.parameter)
    ).filter_by(id=location_id).first()
    
    if not location:
        return jsonify({'error': 'Location not found'}), 404
    
    # Process sensors (already loaded via eager loading)
    sensor_data = []
    for sensor in location.sensors:
        if sensor.parameter:  # Already loaded
            sensor_data.append({
                'id': sensor.id,
                'openaq_id': sensor.openaq_id,
                'parameter': {
                    'id': sensor.parameter.id,
                    'name': sensor.parameter.name,
                    'display_name': sensor.parameter.display_name,
                    'unit': sensor.parameter.unit
                },
                'last_value': float(sensor.last_value) if sensor.last_value else None,
                'last_updated': sensor.last_updated.isoformat() if sensor.last_updated else None
            })
    
    # Calculate simple AQI (preserved from original)
    pm25_sensor = next((s for s in sensor_data if s['parameter']['name'] == 'pm25'), None)
    aqi = calculate_aqi_from_pm25(pm25_sensor['last_value']) if pm25_sensor and pm25_sensor['last_value'] else None
    
    result = {
        'id': location.id,
        'openaq_id': location.openaq_id,
        'name': location.name,
        'locality': location.locality,
        'country_code': location.country_code,
        'latitude': float(location.latitude),
        'longitude': float(location.longitude),
        'is_mobile': location.is_mobile,
        'last_updated': location.last_updated.isoformat() if location.last_updated else None,
        'sensors': sensor_data,
        'aqi': aqi
    }
    
    return jsonify(result)

@api_bp.route('/locations/search', methods=['GET'])
@cache.cached(timeout=600, query_string=True)  # Cache search results
def search_locations():
    """Search locations by name or locality with caching"""
    query_term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query_term:
        return jsonify({'results': []})
    
    # Search by name or locality (preserved original logic)
    locations = Location.query.filter(
        db.or_(
            Location.name.ilike(f'%{query_term}%'),
            Location.locality.ilike(f'%{query_term}%')
        )
    ).limit(limit).all()
    
    result = []
    for loc in locations:
        result.append({
            'id': loc.id,
            'name': loc.name,
            'locality': loc.locality,
            'country_code': loc.country_code,
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude)
        })
    
    return jsonify({'results': result})

@api_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint (preserved)"""
    return jsonify({'message': 'API is working!'})

@api_bp.route('/test-db', methods=['GET'])
def test_db():
    """Test database connection (preserved)"""
    try:
        # Test basic database connection
        location_count = Location.query.count()
        sensor_count = Sensor.query.count()
        parameter_count = Parameter.query.count()
        measurement_count = Measurement.query.count()
        
        return jsonify({
            'status': 'Database connected successfully',
            'counts': {
                'locations': location_count,
                'sensors': sensor_count,
                'parameters': parameter_count,
                'measurements': measurement_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'Database connection failed',
            'error': str(e)
        }), 500

def calculate_aqi_from_pm25(pm25):
    """Simple function to calculate AQI from PM2.5 value (preserved from original)"""
    if pm25 is None:
        return None
        
    # EPA AQI breakpoints for PM2.5
    breakpoints = [
        (0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500)
    ]
    
    for low_conc, high_conc, low_aqi, high_aqi in breakpoints:
        if low_conc <= pm25 <= high_conc:
            aqi = ((high_aqi - low_aqi) / (high_conc - low_conc)) * (pm25 - low_conc) + low_aqi
            return round(aqi)
    
    return None
