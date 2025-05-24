import os
import time
import re
import requests
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from celery.utils.log import get_task_logger
from app.models import db, Location, Parameter, Sensor, Measurement
from app import create_app

logger = get_task_logger(__name__)

# Create app instance for context
app = create_app()

class RateLimiter:
    def __init__(self):
        self.last_request = time.time()
        self.remaining = 60  # Start with max free tier limit
    
    def wait_if_needed(self):
        elapsed = time.time() - self.last_request
        if self.remaining <= 5:  # Leave buffer
            wait_time = 60 - elapsed  # Reset every minute
            if wait_time > 0:
                logger.info(f"Preemptive rate limit wait: {wait_time:.1f}s")
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

def fetch_api_data(url, headers, params):
    """Handle requests with rate limiting and retries"""
    global rate_limiter
    for attempt in range(3):  # Max 3 retries
        rate_limiter.wait_if_needed()
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            rate_limiter.remaining = int(response.headers.get('x-ratelimit-remaining', 60))
            
            if response.status_code == 429:
                reset = int(response.headers.get('x-ratelimit-reset', 60))
                logger.warning(f"Rate limited. Waiting {reset}s...")
                time.sleep(reset + 1)
                continue
                
            if response.status_code == 404:
                logger.warning(f"Resource not found: {url} with params {params}")
                return None
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt+1}/3): {str(e)}")
            time.sleep(2 ** attempt)  # Exponential backoff
    return None

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

def process_sensor(location, sensor_data):
    """Upsert sensor with conflict handling"""
    if location is None:
        logger.warning(f"Location is None for sensor {sensor_data['id']}")
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
            logger.info(f"Created new sensor {sensor.id} for {parameter.name} at {location.name}")
        
        return sensor
    except IntegrityError:
        db.session.rollback()
        return Sensor.query.filter_by(openaq_id=sensor_data['id']).first()

def update_sensor_with_measurement(sensor, measurement):
    """Update sensor with latest measurement data AND create measurement record - NO DATE FILTERING"""
    if sensor is None:
        return
        
    try:
        # Get datetime from measurement
        if 'date' in measurement:
            timestamp = datetime.fromisoformat(measurement['date']['utc'].replace('Z', '+00:00'))
        elif 'datetime' in measurement:
            timestamp = datetime.fromisoformat(measurement['datetime']['utc'].replace('Z', '+00:00'))
        else:
            logger.warning(f"Unknown timestamp format in measurement: {measurement}")
            return
        
        # NO DATE FILTERING - ACCEPT ALL DATA FROM ANY DATE
        # Check if measurement already exists
        existing_measurement = Measurement.query.filter_by(
            sensor_id=sensor.id,
            timestamp=timestamp
        ).first()
        
        if not existing_measurement:
            new_measurement = Measurement(
                sensor_id=sensor.id,
                value=float(measurement['value']),
                timestamp=timestamp
            )
            db.session.add(new_measurement)
            logger.info(f"✅ Created measurement for sensor {sensor.openaq_id}: {measurement['value']} at {timestamp}")
        
        # Update sensor's last value if this is newer
        sensor_last_updated = sensor.last_updated
        if sensor_last_updated and sensor_last_updated.tzinfo is None:
            sensor_last_updated = sensor_last_updated.replace(tzinfo=timezone.utc)
        
        if not sensor.last_updated or timestamp > sensor_last_updated:
            sensor.last_value = float(measurement['value'])
            sensor.last_updated = timestamp
            logger.info(f"✅ Updated sensor {sensor.openaq_id} last_value to {measurement['value']} at {timestamp}")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating sensor with measurement: {e}")

def fetch_latest_measurements(location_id):
    """Fetch ONLY latest measurements for a location - NO HISTORICAL DATA"""
    url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    headers = {'X-API-Key': os.getenv('OPENAQ_API_KEY')}
    
    data = fetch_api_data(url, headers, {})
    if not data or 'results' not in data:
        logger.warning(f"No latest data for location {location_id}")
        return []
        
    return data['results']

def process_location(loc_data, fetch_history=False):
    """Process location with all related data - NO HISTORICAL FETCHING"""
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
            logger.info(f"Created new location: {location.name}")
        else:
            location.name = loc_data['name']
            location.locality = loc_data.get('locality')
            location.latitude = loc_data['coordinates']['latitude']
            location.longitude = loc_data['coordinates']['longitude']
            location.is_mobile = loc_data['isMobile']
            location.last_updated = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Updated location: {location.name}")
    except IntegrityError:
        db.session.rollback()
        location = Location.query.filter_by(openaq_id=loc_data['id']).first()
    
    if location is None:
        logger.error(f"Could not create or retrieve location for ID {loc_data['id']}")
        return
    
    # Process sensors
    sensor_map = {}  # Map OpenAQ sensor IDs to our DB sensors
    
    for sensor_data in loc_data.get('sensors', []):
        sensor = process_sensor(location, sensor_data)
        if sensor:
            sensor_map[sensor_data['id']] = sensor
    
    # Fetch ONLY latest measurements for this location - NO HISTORICAL DATA
    latest_measurements = fetch_latest_measurements(loc_data['id'])
    for measurement in latest_measurements:
        sensor_id = measurement.get('sensorsId')
        if sensor_id in sensor_map:
            update_sensor_with_measurement(sensor_map[sensor_id], measurement)

# Import celery from celery_app after app is created
from celery_app import celery

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def fetch_locations_page(self, page_number, fetch_history=False):
    """Fetch and process a single page of locations - NO HISTORICAL DATA"""
    with app.app_context():
        try:
            logger.info(f"Starting to fetch locations page {page_number}")
            
            url = "https://api.openaq.org/v3/locations"
            headers = {'X-API-Key': os.getenv('OPENAQ_API_KEY')}
            
            params = {
                'countries_id': 155,  # US country ID
                'limit': 1000,
                'page': page_number,
                'sort': 'id',  # Ensure consistent pagination
                'order': 'asc'
            }
            
            data = fetch_api_data(url, headers, params)
            if not data or 'results' not in data or len(data['results']) == 0:
                logger.info(f"No data returned for page {page_number}")
                return {
                    'status': 'no_data',
                    'page': page_number,
                    'locations_processed': 0
                }

            # Process locations on this page - NO HISTORICAL DATA FETCHING
            locations_processed = 0
            
            for loc in data['results']:
                try:
                    process_location(loc, fetch_history=False)  # NEVER fetch history in tasks
                    locations_processed += 1
                    
                    if locations_processed % 10 == 0:
                        logger.info(f"Page {page_number}: Processed {locations_processed}/{len(data['results'])} locations")
                        
                except Exception as e:
                    logger.error(f"Error processing location {loc.get('id', 'unknown')}: {e}")
                    continue

            result = {
                'status': 'success',
                'page': page_number,
                'locations_processed': locations_processed,
                'total_locations_on_page': len(data['results']),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Page {page_number} completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Critical error processing page {page_number}: {str(e)}")
            raise

@celery.task(bind=True)
def fetch_all_locations(self, fetch_history_pages=None):
    """Orchestrate fetching all location pages - ALL 4,877 LOCATIONS - NO HISTORICAL DATA"""
    with app.app_context():
        try:
            logger.info("Starting full location fetch for ALL 4,877 locations...")
            
            total_pages = 5  # We know there are 5 pages to get all 4,877 locations
            
            logger.info(f"Scheduling {total_pages} page tasks to process ALL 4,877 locations (NO HISTORICAL DATA)")
            
            # Schedule page tasks - NO HISTORICAL DATA FETCHING
            for page in range(1, total_pages + 1):
                fetch_locations_page.delay(page, fetch_history=False)  # NEVER fetch history
                logger.info(f"Scheduled page {page} (latest data only)")
            
            return {
                'status': 'scheduled',
                'total_pages': total_pages,
                'total_locations': 4877,
                'note': 'Latest data only - no historical fetching',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling location fetch: {str(e)}")
            raise

@celery.task(bind=True)
def fetch_all_measurements_orchestrator(self):
    """Process ALL 4,877 locations by scheduling multiple batch tasks - LATEST DATA ONLY"""
    with app.app_context():
        try:
            # Get total count of ALL locations
            total_locations = Location.query.count()
            batch_size = 100
            total_batches = (total_locations + batch_size - 1) // batch_size
            
            logger.info(f"Total locations: {total_locations}")
            logger.info(f"Scheduling {total_batches} batches of {batch_size} to process ALL locations (LATEST DATA ONLY)")
            
            # Schedule batch tasks with offsets to cover ALL locations
            for i in range(total_batches):
                offset = i * batch_size
                fetch_measurements_with_offset.delay(offset=offset, batch_size=batch_size)
                logger.info(f"Scheduled batch {i+1}/{total_batches} (offset {offset})")
            
            return {
                'status': 'scheduled',
                'total_locations': total_locations,
                'total_batches': total_batches,
                'batch_size': batch_size,
                'note': 'Latest measurements only - no historical fetching',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            raise

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def fetch_measurements_with_offset(self, offset=0, batch_size=100):
    """Fetch LATEST measurements for a batch of ALL locations - NO HISTORICAL DATA"""
    with app.app_context():
        try:
            logger.info(f"Processing batch: offset={offset}, batch_size={batch_size} (LATEST DATA ONLY)")
            
            # Get ALL locations with offset
            locations = db.session.query(Location).offset(offset).limit(batch_size).all()
            
            if not locations:
                logger.info(f"No more locations at offset {offset}")
                return {'status': 'no_more_locations', 'offset': offset}
            
            logger.info(f"Processing {len(locations)} locations for LATEST measurements only")
            
            processed_count = 0
            new_measurements = 0
            locations_with_data = 0
            
            for location in locations:
                try:
                    # Fetch ONLY latest measurements for this location - NO HISTORICAL DATA
                    latest_measurements = fetch_latest_measurements(location.openaq_id)
                    
                    if not latest_measurements:
                        logger.debug(f"No latest measurements for location {location.id} ({location.name})")
                        processed_count += 1
                        continue
                    
                    locations_with_data += 1
                    
                    # Get sensor mapping for this location
                    sensors = Sensor.query.filter_by(location_id=location.id).all()
                    sensor_map = {sensor.openaq_id: sensor for sensor in sensors}
                    
                    # Process ONLY latest measurements - NO HISTORICAL DATA
                    for measurement in latest_measurements:
                        sensor_id = measurement.get('sensorsId')
                        if sensor_id in sensor_map:
                            update_sensor_with_measurement(sensor_map[sensor_id], measurement)
                            new_measurements += 1
                        else:
                            logger.debug(f"Sensor {sensor_id} not found in location {location.id}")
                    
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        logger.info(f"Batch {offset}: Processed {processed_count}/{len(locations)} locations, {locations_with_data} had data")
                    
                except Exception as e:
                    logger.error(f"Error processing location {location.id}: {e}")
                    processed_count += 1
                    continue
            
            result = {
                'status': 'success',
                'offset': offset,
                'batch_size': batch_size,
                'locations_processed': processed_count,
                'locations_with_data': locations_with_data,
                'new_measurements': new_measurements,
                'note': 'Latest measurements only - no historical data',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Batch {offset} completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in batch at offset {offset}: {str(e)}")
            raise

# Configure periodic tasks - NO CLEANUP TASKS
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'fetch-latest-measurements-every-2-hours': {
        'task': 'app.tasks.fetch_all_measurements_orchestrator',  # LATEST DATA ONLY
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'update-all-locations-weekly': {
        'task': 'app.tasks.fetch_all_locations',  # Gets all 4,877 locations
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2 AM
    },
    # NO CLEANUP TASKS - DATA PRESERVED FOREVER
}

celery.conf.timezone = 'UTC'
