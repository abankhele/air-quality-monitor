from flask import jsonify
from sqlalchemy import func, desc
from app.models import db, Location, Parameter, Sensor, Measurement
from app.api import api_bp
from datetime import datetime, timedelta

@api_bp.route('/stats/overview', methods=['GET'])
def get_stats_overview():
    """Get overview statistics for the dashboard"""
    # Count total locations
    location_count = Location.query.count()
    
    # Count total sensors
    sensor_count = Sensor.query.count()
    
    # Count total measurements
    measurement_count = Measurement.query.count()
    
    # Get top 5 locations with most sensors
    top_locations = db.session.query(
        Location.id, Location.name, func.count(Sensor.id).label('sensor_count')
    ).join(Sensor).group_by(Location.id).order_by(desc('sensor_count')).limit(5).all()
    
    top_locations_data = [
        {'id': loc.id, 'name': loc.name, 'sensor_count': loc.sensor_count}
        for loc in top_locations
    ]
    
    # Get parameter distribution
    parameter_stats = db.session.query(
        Parameter.id, Parameter.name, Parameter.display_name,
        func.count(Sensor.id).label('sensor_count')
    ).join(Sensor).group_by(Parameter.id).order_by(desc('sensor_count')).all()
    
    parameter_data = [
        {
            'id': param.id,
            'name': param.name,
            'display_name': param.display_name,
            'sensor_count': param.sensor_count
        }
        for param in parameter_stats
    ]
    
    # Get recent measurement count (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_count = Measurement.query.filter(Measurement.timestamp >= yesterday).count()
    
    return jsonify({
        'location_count': location_count,
        'sensor_count': sensor_count,
        'measurement_count': measurement_count,
        'recent_measurement_count': recent_count,
        'top_locations': top_locations_data,
        'parameter_distribution': parameter_data
    })
