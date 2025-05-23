from app import create_app
from app.database import db

def add_simple_indexes():
    app = create_app()
    
    with app.app_context():
        print("Adding database indexes (without CONCURRENTLY)...")
        
        # Simpler index creation (works on all PostgreSQL versions)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sensors_location_id ON sensors(location_id);",
            "CREATE INDEX IF NOT EXISTS idx_sensors_parameter_id ON sensors(parameter_id);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_sensor_id ON measurements(sensor_id);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_timestamp ON measurements(timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_locations_lat_lng ON locations(latitude, longitude);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_sensor_timestamp ON measurements(sensor_id, timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_sensors_location_parameter ON sensors(location_id, parameter_id);",
            "CREATE INDEX IF NOT EXISTS idx_locations_bounds ON locations(latitude, longitude, country_code);"
        ]
        
        for index_sql in indexes:
            try:
                print(f"Creating index: {index_sql}")
                db.session.execute(db.text(index_sql))
                db.session.commit()
                print("✅ Success")
            except Exception as e:
                print(f"❌ Error: {e}")
                db.session.rollback()
        
        print("Index creation completed!")

if __name__ == "__main__":
    add_simple_indexes()
