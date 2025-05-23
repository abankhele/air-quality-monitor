from flask import jsonify, request
from sqlalchemy import func
from app.models import db, Location, Sensor, Parameter, Measurement
from app.api import api_bp
from app.api.utils import parse_bounds


@api_bp.route('/locations', methods=['GET'])
def get_locations():
    """Get all locations with optional filtering"""
    # Parse query parameters
    bounds = parse_bounds(request)
    limit = request.args.get('limit', 1000, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build query
    query = Location.query
    
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
    
    # Format response
    result = []
    for loc in locations:
        # Get latest measurements for AQI calculation
        sensors = Sensor.query.filter_by(location_id=loc.id).all()
        sensor_data = []
        
        for sensor in sensors:
            parameter = Parameter.query.get(sensor.parameter_id)
            sensor_data.append({
                'id': sensor.id,
                'openaq_id': sensor.openaq_id,
                'parameter': {
                    'id': parameter.id,
                    'name': parameter.name,
                    'display_name': parameter.display_name,
                    'unit': parameter.unit
                },
                'last_value': float(sensor.last_value) if sensor.last_value else None,
                'last_updated': sensor.last_updated.isoformat() if sensor.last_updated else None
            })
        
        # Calculate simple AQI (just for demonstration)
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
def get_location(location_id):
    """Get details for a specific location"""
    location = Location.query.get_or_404(location_id)
    
    # Get sensors for this location
    sensors = Sensor.query.filter_by(location_id=location.id).all()
    sensor_data = []
    
    for sensor in sensors:
        parameter = Parameter.query.get(sensor.parameter_id)
        sensor_data.append({
            'id': sensor.id,
            'openaq_id': sensor.openaq_id,
            'parameter': {
                'id': parameter.id,
                'name': parameter.name,
                'display_name': parameter.display_name,
                'unit': parameter.unit
            },
            'last_value': float(sensor.last_value) if sensor.last_value else None,
            'last_updated': sensor.last_updated.isoformat() if sensor.last_updated else None
        })
    
    # Calculate simple AQI
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
def search_locations():
    """Search locations by name or locality"""
    query_term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query_term:
        return jsonify({'results': []})
    
    # Search by name or locality
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

def calculate_aqi_from_pm25(pm25):
    """Simple function to calculate AQI from PM2.5 value"""
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
@api_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({'message': 'API is working!'})

