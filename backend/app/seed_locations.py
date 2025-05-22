import os
import time
import re
import requests
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.models import db, Location, Parameter, Sensor, Measurement

app = create_app()

# Rate limit tracking
class RateLimiter:
    def __init__(self):
        self.last_request = time.time()
        self.remaining = 60  # Start with max free tier limit
    
    def wait_if_needed(self):
        elapsed = time.time() - self.last_request
        if self.remaining <= 5:  # Leave buffer
            wait_time = 60 - elapsed  # Reset every minute
            if wait_time > 0:
                print(f"Preemptive rate limit wait: {wait_time:.1f}s")
                time.sleep(wait_time)
                self.remaining = 60  # Reset counter
        self.last_request = time.time()

rate_limiter = RateLimiter()

def parse_found_value(found):
    """Handle OpenAQ's 'found' values which can be strings like '>1000'"""
    if isinstance(found, str):
        match = re.search(r'\d+', found)
        return int(match.group()) if match else 0
    return found

def process_parameter(param_data):
    """Upsert parameter with conflict handling"""
    try:
        parameter = Parameter.query.filter_by(name=param_data['name']).first()
        if not parameter:
            parameter = Parameter(
                name=param_data['name'],
                display_name=param_data.get('displayName', param_data['name']),
                unit=param_data['units']
            )
            db.session.add(parameter)
            db.session.commit()
        return parameter
    except IntegrityError:
        db.session.rollback()
        return Parameter.query.filter_by(name=param_data['name']).first()

def fetch_api_data(url, headers, params):
    """Handle requests with rate limiting and retries"""
    global rate_limiter
    for attempt in range(3):  # Max 3 retries
        rate_limiter.wait_if_needed()
        try:
            response = requests.get(url, headers=headers, params=params)
            rate_limiter.remaining = int(response.headers.get('x-ratelimit-remaining', 60))
            
            if response.status_code == 429:
                reset = int(response.headers.get('x-ratelimit-reset', 60))
                print(f"Rate limited. Waiting {reset}s...")
                time.sleep(reset + 1)
                continue
                
            if response.status_code == 404:
                print(f"Resource not found: {url} with params {params}")
                return None
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt+1}/3): {str(e)}")
            time.sleep(2 ** attempt)  # Exponential backoff
    return None

def fetch_latest_measurements(location_id):
    """Fetch latest measurements for a location using the /latest endpoint"""
    url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    headers = {'X-API-Key': os.getenv('OPENAQ_API_KEY')}
    
    data = fetch_api_data(url, headers, {})
    if not data or 'results' not in data:
        print(f"No latest data for location {location_id}")
        return []
        
    return data['results']

def fetch_historical_measurements(location_id, parameter_name):
    """Fetch historical measurements for a location/parameter pair"""
    url = "https://api.openaq.org/v3/measurements"
    headers = {'X-API-Key': os.getenv('OPENAQ_API_KEY')}
    date_from = (datetime.now(timezone.utc) - timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    params = {
        'location_id': location_id,
        'parameter': parameter_name,
        'date_from': date_from,
        'limit': 1000,
        'page': 1
    }
    
    all_measurements = []
    while True:
        data = fetch_api_data(url, headers, params)
        if not data or 'results' not in data:
            break
            
        all_measurements.extend(data['results'])
        
        # Pagination control
        meta = data.get('meta', {})
        found = parse_found_value(meta.get('found', 0))
        if params['page'] * params['limit'] >= found or len(data['results']) == 0:
            break
        params['page'] += 1
        time.sleep(0.5)  # Brief pause between pages
    
    return all_measurements

def update_sensor_with_measurement(sensor, measurement):
    """Update sensor with latest measurement data"""
    if sensor is None:
        return
        
    try:
        # Get datetime from measurement
        if 'date' in measurement:
            # Format from /measurements endpoint
            timestamp = datetime.fromisoformat(measurement['date']['utc'].replace('Z', '+00:00'))
        elif 'datetime' in measurement:
            # Format from /latest endpoint
            timestamp = datetime.fromisoformat(measurement['datetime']['utc'].replace('Z', '+00:00'))
        else:
            print(f"Unknown timestamp format in measurement: {measurement}")
            return
            
        # Check if measurement already exists
        if not Measurement.query.filter_by(sensor_id=sensor.id, timestamp=timestamp).first():
            db.session.add(Measurement(
                sensor_id=sensor.id,
                value=measurement['value'],
                timestamp=timestamp
            ))
            db.session.commit()
            print(f"Added new measurement for sensor {sensor.openaq_id}")
        
        # Update sensor's last value
        sensor.last_value = measurement['value']
        sensor.last_updated = timestamp
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating sensor with measurement: {e}")

def process_sensor(location, sensor_data):
    """Upsert sensor with conflict handling"""
    if location is None:
        print(f"Warning: Location is None for sensor {sensor_data['id']}")
        return None
        
    parameter = process_parameter(sensor_data['parameter'])
    
    try:
        sensor = Sensor.query.filter_by(openaq_id=sensor_data['id']).first()
        if not sensor:
            sensor = Sensor(
                openaq_id=sensor_data['id'],
                location_id=location.id,
                parameter_id=parameter.id
            )
            db.session.add(sensor)
            db.session.commit()
            print(f"Created new sensor {sensor.id} for {parameter.name} at {location.name}")
        
        return sensor
    except IntegrityError:
        db.session.rollback()
        return Sensor.query.filter_by(openaq_id=sensor_data['id']).first()

def process_location(loc_data, fetch_history=False):
    """Process location with all related data"""
    # Upsert location
    try:
        location = Location.query.filter_by(openaq_id=loc_data['id']).first()
        if not location:
            location = Location(
                openaq_id=loc_data['id'],
                name=loc_data['name'],
                locality=loc_data.get('locality'),
                country_code=loc_data['country']['code'],
                latitude=loc_data['coordinates']['latitude'],
                longitude=loc_data['coordinates']['longitude'],
                is_mobile=loc_data['isMobile']
            )
            db.session.add(location)
            db.session.commit()
            print(f"Created new location: {location.name}")
        else:
            location.name = loc_data['name']
            location.locality = loc_data.get('locality')
            location.latitude = loc_data['coordinates']['latitude']
            location.longitude = loc_data['coordinates']['longitude']
            location.is_mobile = loc_data['isMobile']
            location.last_updated = datetime.now(timezone.utc)
            db.session.commit()
            print(f"Updated location: {location.name}")
    except IntegrityError:
        db.session.rollback()
        location = Location.query.filter_by(openaq_id=loc_data['id']).first()
    
    if location is None:
        print(f"Error: Could not create or retrieve location for ID {loc_data['id']}")
        return
    
    # Process sensors
    sensor_map = {}  # Map OpenAQ sensor IDs to our DB sensors
    parameter_map = {}  # Map parameter names to parameter objects
    
    for sensor_data in loc_data.get('sensors', []):
        sensor = process_sensor(location, sensor_data)
        if sensor:
            sensor_map[sensor_data['id']] = sensor
            parameter = process_parameter(sensor_data['parameter'])
            parameter_map[parameter.name] = parameter
    
    # Fetch latest measurements for this location
    latest_measurements = fetch_latest_measurements(loc_data['id'])
    for measurement in latest_measurements:
        sensor_id = measurement.get('sensorsId')
        if sensor_id in sensor_map:
            update_sensor_with_measurement(sensor_map[sensor_id], measurement)
    
    # Fetch historical data if requested
    if fetch_history:
        for param_name, parameter in parameter_map.items():
            historical = fetch_historical_measurements(loc_data['id'], param_name)
            for measurement in historical:
                # Find the right sensor for this parameter
                for sensor_id, sensor in sensor_map.items():
                    if sensor.parameter_id == parameter.id:
                        update_sensor_with_measurement(sensor, measurement)
                        break

def fetch_locations(start_page=1, end_page=None, fetch_history_pages=None):
    """Main function to fetch US locations with pagination control"""
    url = "https://api.openaq.org/v3/locations"
    headers = {'X-API-Key': os.getenv('OPENAQ_API_KEY')}
    
    # Set defaults
    current_page = start_page
    total_pages = 5  # We now know there are 5 pages (4891 locations)
    limit = 1000
    
    # If end_page is specified, use it
    if end_page:
        total_pages = min(end_page, total_pages)
    
    # Default to fetching history for page 1 only
    if fetch_history_pages is None:
        fetch_history_pages = [1]
    
    with app.app_context():
        while current_page <= total_pages:
            params = {
                'countries_id': 155,  # US country ID
                'limit': limit,
                'page': current_page,
                'sort': 'id',  # Ensure consistent pagination
                'order': 'asc'
            }
            
            data = fetch_api_data(url, headers, params)
            if not data or 'results' not in data or len(data['results']) == 0:
                print(f"No data returned for page {current_page}")
                break

            # Process locations on this page
            for loc in data['results']:
                # Fetch historical data only for specified pages
                fetch_history = current_page in fetch_history_pages
                process_location(loc, fetch_history)

            # Print progress
            print(f"Processed page {current_page} with {len(data['results'])} locations")
            
            # Move to next page
            current_page += 1

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    # You can customize which pages to process and which to fetch history for
    # For example, to process pages 2-5 with no historical data:
    # fetch_locations(start_page=2, end_page=5, fetch_history_pages=[])
    
    # Or to process all pages with historical data for page 1:
    fetch_locations(start_page=1, end_page=5, fetch_history_pages=[])