#!/usr/bin/env python
import click
from app import create_app
from app.tasks import (
    fetch_all_measurements_orchestrator, 
    fetch_all_locations, 
    fetch_measurements_with_offset,
    fetch_locations_page
)

app = create_app()

@click.group()
def cli():
    """Air Quality Management Commands"""
    pass

@cli.command()
def fetch_data():
    """Manually trigger latest measurements fetch for ALL 4,877 locations"""
    with app.app_context():
        result = fetch_all_measurements_orchestrator.delay()
        click.echo(f"Started ALL 4,877 locations measurements task: {result.id}")
        click.echo("This will process all locations in batches of 100. Monitor in Flower at http://localhost:5555")

@cli.command()
def update_locs():
    """Manually trigger location update for ALL 4,877 locations"""
    with app.app_context():
        result = fetch_all_locations.delay(fetch_history_pages=[1])
        click.echo(f"Started ALL 4,877 locations update task: {result.id}")
        click.echo("This will fetch/update all US locations from OpenAQ API")

@cli.command()
@click.option('--offset', default=0, help='Starting offset for batch processing')
@click.option('--batch-size', default=100, help='Number of locations to process in this batch')
def fetch_batch(offset, batch_size):
    """Manually trigger a single batch of measurements fetch"""
    with app.app_context():
        result = fetch_measurements_with_offset.delay(offset=offset, batch_size=batch_size)
        click.echo(f"Started batch measurements task: {result.id}")
        click.echo(f"Processing locations {offset} to {offset + batch_size}")

@cli.command()
@click.option('--page', default=1, help='Page number to fetch (1-5)')
@click.option('--history', is_flag=True, help='Fetch historical data for this page')
def fetch_page(page, history):
    """Manually trigger a single page of locations fetch"""
    with app.app_context():
        result = fetch_locations_page.delay(page, fetch_history=history)
        click.echo(f"Started locations page {page} task: {result.id}")
        click.echo(f"Fetching page {page} with history: {history}")

@cli.command()
def status():
    """Show current data status - NO DATA MODIFICATION"""
    with app.app_context():
        from app.models import Location, Sensor, Measurement
        from datetime import datetime, timezone
        
        # Basic counts
        total_locations = Location.query.count()
        total_sensors = Sensor.query.count()
        total_measurements = Measurement.query.count()
        
        # Fresh data counts (after May 21, 2025)
        cutoff_date = datetime(2025, 5, 21, tzinfo=timezone.utc)
        fresh_measurements = Measurement.query.filter(Measurement.timestamp >= cutoff_date).count()
        
        # Count sensors with fresh data
        fresh_sensors = Sensor.query.filter(
            Sensor.last_updated >= cutoff_date
        ).count()
        
        # Count sensors with any data
        sensors_with_data = Sensor.query.filter(
            Sensor.last_value.is_not(None)
        ).count()
        
        click.echo("Current Data Status:")
        click.echo(f"Total Locations: {total_locations}")
        click.echo(f"Total Sensors: {total_sensors}")
        click.echo(f"Sensors with Data: {sensors_with_data}")
        click.echo(f"Total Measurements: {total_measurements}")
        click.echo(f"Fresh Measurements (May 21+): {fresh_measurements}")
        click.echo(f"Fresh Sensors (May 21+): {fresh_sensors}")
        
        if total_sensors > 0:
            fresh_percentage = (fresh_sensors / total_sensors * 100) if total_sensors > 0 else 0
            data_percentage = (sensors_with_data / total_sensors * 100) if total_sensors > 0 else 0
            click.echo(f"  Fresh Data Coverage: {fresh_percentage:.1f}%")
            click.echo(f"  Overall Data Coverage: {data_percentage:.1f}%")

@cli.command()
def test_location():
    """Test data fetching for a specific location - NO DATA MODIFICATION"""
    with app.app_context():
        from app.tasks import fetch_latest_measurements
        
        # Test with a known location
        test_location_id = 4700  # Manzanita Ave - known to have data
        
        click.echo(f"Testing data fetch for location {test_location_id}...")
        
        try:
            measurements = fetch_latest_measurements(test_location_id)
            click.echo(f"Found {len(measurements)} measurements")
            
            if measurements:
                for measurement in measurements[:3]:  # Show first 3
                    click.echo(f"  - {measurement.get('parameter', {}).get('name', 'unknown')}: {measurement.get('value', 'N/A')}")
            else:
                click.echo(" No measurements found")
                
        except Exception as e:
            click.echo(f" Error: {str(e)}")

@cli.command()
def check_fresh_coverage():
    """Check how many locations have fresh data - NO DATA MODIFICATION"""
    with app.app_context():
        from app.models import Location, Sensor
        from datetime import datetime, timezone
        
        cutoff_date = datetime(2025, 5, 21, tzinfo=timezone.utc)
        
        # Get locations with fresh sensor data
        locations_with_fresh_data = db.session.query(Location.id).join(Sensor).filter(
            Sensor.last_updated >= cutoff_date
        ).distinct().count()
        
        total_locations = Location.query.count()
        
        click.echo(f"Fresh Data Coverage:")
        click.echo(f"Locations with fresh data: {locations_with_fresh_data}")
        click.echo(f"Total locations: {total_locations}")
        click.echo(f"Coverage: {(locations_with_fresh_data/total_locations*100):.1f}%")

if __name__ == '__main__':
    cli()
