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
            logger.warning(f"Unknown timestamp format in measurement: {measurement}")
            return
            
        # Check if measurement already exists
        if not Measurement.query.filter_by(sensor_id=sensor.id, timestamp=timestamp).first():
            db.session.add(Measurement(
                sensor_id=sensor.id,
                value=measurement['value'],
                timestamp=timestamp
            ))
            db.session.commit()
            logger.info(f"Added new measurement for sensor {sensor.openaq_id}")
        
        # Update sensor's last value
        sensor.last_value = measurement['value']
        sensor.last_updated = timestamp
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating sensor with measurement: {e}")

def fetch_latest_measurements(location_id):
    """Fetch latest measurements for a location using the /latest endpoint"""
    url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    headers = {'X-API-Key': os.getenv('OPENAQ_API_KEY')}
    
    data = fetch_api_data(url, headers, {})
    if not data or 'results' not in data:
        logger.warning(f"No latest data for location {location_id}")
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

# Import celery from celery_app after app is created
from celery_app import celery

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def fetch_locations_page(self, page_number, fetch_history=False):
    """Fetch and process a single page of locations"""
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

            # Process locations on this page
            locations_processed = 0
            
            for loc in data['results']:
                try:
                    process_location(loc, fetch_history)
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
                'fetch_history': fetch_history,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Page {page_number} completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Critical error processing page {page_number}: {str(e)}")
            raise

@celery.task(bind=True)
def fetch_all_locations(self, fetch_history_pages=None):
    """Orchestrate fetching all location pages - ALL 4,877 LOCATIONS"""
    with app.app_context():
        try:
            logger.info("Starting full location fetch for ALL 4,877 locations...")
            
            # Default to fetching history for page 1 only
            if fetch_history_pages is None:
                fetch_history_pages = [1]
            
            total_pages = 5  # We know there are 5 pages to get all 4,877 locations
            
            logger.info(f"Scheduling {total_pages} page tasks to process ALL 4,877 locations, history for pages: {fetch_history_pages}")
            
            # Schedule page tasks
            for page in range(1, total_pages + 1):
                fetch_history = page in fetch_history_pages
                fetch_locations_page.delay(page, fetch_history)
                logger.info(f"Scheduled page {page} (history: {fetch_history})")
            
            return {
                'status': 'scheduled',
                'total_pages': total_pages,
                'total_locations': 4877,
                'fetch_history_pages': fetch_history_pages,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling location fetch: {str(e)}")
            raise

@celery.task(bind=True)
def fetch_all_measurements_orchestrator(self):
    """Process ALL locations with sensors by scheduling multiple batch tasks"""
    with app.app_context():
        try:
            # Get total count of locations with sensors
            total_locations = db.session.query(Location).join(Sensor).distinct().count()
            batch_size = 100
            total_batches = (total_locations + batch_size - 1) // batch_size
            
            logger.info(f"Total locations with sensors: {total_locations}")
            logger.info(f"Scheduling {total_batches} batches of {batch_size} to process ALL locations")
            
            # Schedule batch tasks with offsets
            for i in range(total_batches):
                offset = i * batch_size
                fetch_measurements_with_offset.delay(offset=offset, batch_size=batch_size)
                logger.info(f"Scheduled batch {i+1}/{total_batches} (offset {offset})")
            
            return {
                'status': 'scheduled',
                'total_locations': total_locations,
                'total_batches': total_batches,
                'batch_size': batch_size,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            raise

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def fetch_measurements_with_offset(self, offset=0, batch_size=100):
    """Fetch measurements for a batch of locations with offset"""
    with app.app_context():
        try:
            logger.info(f"Processing batch: offset={offset}, batch_size={batch_size}")
            
            # Get locations with offset
            locations = db.session.query(Location).join(Sensor).distinct().offset(offset).limit(batch_size).all()
            
            if not locations:
                logger.info(f"No more locations at offset {offset}")
                return {'status': 'no_more_locations', 'offset': offset}
            
            logger.info(f"Processing {len(locations)} locations for latest measurements")
            
            processed_count = 0
            new_measurements = 0
            
            for location in locations:
                try:
                    # Fetch latest measurements for this location
                    latest_measurements = fetch_latest_measurements(location.openaq_id)
                    
                    # Get sensor mapping for this location
                    sensors = Sensor.query.filter_by(location_id=location.id).all()
                    sensor_map = {sensor.openaq_id: sensor for sensor in sensors}
                    
                    # Process measurements
                    for measurement in latest_measurements:
                        sensor_id = measurement.get('sensorsId')
                        if sensor_id in sensor_map:
                            update_sensor_with_measurement(sensor_map[sensor_id], measurement)
                            new_measurements += 1
                    
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        logger.info(f"Batch {offset}: Processed {processed_count}/{len(locations)} locations")
                    
                except Exception as e:
                    logger.error(f"Error processing location {location.id}: {e}")
                    continue
            
            result = {
                'status': 'success',
                'offset': offset,
                'batch_size': batch_size,
                'locations_processed': processed_count,
                'new_measurements': new_measurements,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Batch {offset} completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in batch at offset {offset}: {str(e)}")
            raise

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 300})
def fetch_latest_measurements_batch(self, batch_size=100):
    """Fetch latest measurements for existing locations in batches - PROCESSES ALL LOCATIONS"""
    with app.app_context():
        try:
            logger.info(f"Starting latest measurements fetch (batch size: {batch_size})")
            
            if batch_size is None:
                # Get ALL locations with sensors
                locations = db.session.query(Location).join(Sensor).distinct().all()
                logger.info(f"Processing ALL {len(locations)} locations with sensors")
            else:
                # Get limited batch
                locations = db.session.query(Location).join(Sensor).distinct().limit(batch_size).all()
                logger.info(f"Processing {len(locations)} locations for latest measurements")
            
            if not locations:
                logger.info("No locations with sensors found")
                return {'status': 'no_locations', 'processed': 0}
            
            processed_count = 0
            new_measurements = 0
            
            for location in locations:
                try:
                    # Fetch latest measurements for this location
                    latest_measurements = fetch_latest_measurements(location.openaq_id)
                    
                    # Get sensor mapping for this location
                    sensors = Sensor.query.filter_by(location_id=location.id).all()
                    sensor_map = {sensor.openaq_id: sensor for sensor in sensors}
                    
                    # Process measurements
                    for measurement in latest_measurements:
                        sensor_id = measurement.get('sensorsId')
                        if sensor_id in sensor_map:
                            update_sensor_with_measurement(sensor_map[sensor_id], measurement)
                            new_measurements += 1
                    
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        logger.info(f"Processed {processed_count}/{len(locations)} locations")
                    
                except Exception as e:
                    logger.error(f"Error processing location {location.id}: {e}")
                    continue
            
            result = {
                'status': 'success',
                'locations_processed': processed_count,
                'new_measurements': new_measurements,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Latest measurements batch completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Critical error in latest measurements batch: {str(e)}")
            raise

@celery.task(bind=True)
def cleanup_old_measurements(self):
    """Clean up measurements older than 90 days"""
    with app.app_context():
        try:
            logger.info("Starting cleanup of old measurements...")
            
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            deleted_count = Measurement.query.filter(
                Measurement.timestamp < cutoff_date
            ).delete()
            
            db.session.commit()
            logger.info(f"Deleted {deleted_count} measurements older than {cutoff_date}")
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_measurements: {str(e)}")
            db.session.rollback()
            raise

# Configure periodic tasks
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'fetch-latest-measurements-every-2-hours': {
        'task': 'app.tasks.fetch_all_measurements_orchestrator',  # Use orchestrator to get ALL locations
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'update-all-locations-weekly': {
        'task': 'app.tasks.fetch_all_locations',  # Gets all 4,877 locations
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2 AM
    },
    'cleanup-old-data-monthly': {
        'task': 'app.tasks.cleanup_old_measurements',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # Monthly on 1st at 3 AM
    },
}

celery.conf.timezone = 'UTC'
