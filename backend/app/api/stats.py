from flask import jsonify
from sqlalchemy import func, desc
from app.database import db
from app.models import Location, Parameter, Sensor, Measurement
from app.api import api_bp
from datetime import datetime, timedelta
from app import cache

@api_bp.route('/stats/overview', methods=['GET'])
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_overview_stats():
    """Get overview statistics for the dashboard"""
    try:
        # Basic counts
        location_count = Location.query.count()
        sensor_count = Sensor.query.count()
        parameter_count = Parameter.query.count()
        measurement_count = Measurement.query.count()
        
        # Recent measurements (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_measurement_count = Measurement.query.filter(
            Measurement.timestamp >= seven_days_ago
        ).count()
        
        # Active sensors (sensors with measurements in last 7 days) - FIXED QUERY
        active_sensors = db.session.query(Sensor.id).select_from(Sensor).join(Measurement).filter(
            Measurement.timestamp >= seven_days_ago
        ).distinct().count()
        
        # Top parameters by measurement count - FIXED QUERY
        parameter_stats = db.session.query(
            Parameter.name,
            Parameter.display_name,
            func.count(Measurement.id).label('measurement_count')
        ).select_from(Parameter).join(Sensor).join(Measurement).group_by(
            Parameter.id, Parameter.name, Parameter.display_name
        ).order_by(desc('measurement_count')).limit(10).all()
        
        # Locations by country
        country_stats = db.session.query(
            Location.country_code,
            func.count(Location.id).label('location_count')
        ).group_by(Location.country_code).order_by(desc('location_count')).all()
        
        result = {
            'location_count': location_count,
            'sensor_count': sensor_count,
            'parameter_count': parameter_count,
            'measurement_count': measurement_count,
            'recent_measurement_count': recent_measurement_count,
            'active_sensors': active_sensors,
            'parameter_distribution': [
                {
                    'name': stat.name,
                    'display_name': stat.display_name,
                    'measurement_count': stat.measurement_count
                }
                for stat in parameter_stats
            ],
            'country_distribution': [
                {
                    'country_code': stat.country_code,
                    'location_count': stat.location_count
                }
                for stat in country_stats
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
