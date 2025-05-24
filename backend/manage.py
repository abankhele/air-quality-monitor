#!/usr/bin/env python
import click
from app import create_app
from app.models import db
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
        click.echo("⚠️  NOTE: This fetches LATEST data only, not historical data")

@cli.command()
def update_locs():
    """Manually trigger location update for ALL 4,877 locations"""
    with app.app_context():
        result = fetch_all_locations.delay()
        click.echo(f"Started ALL 4,877 locations update task: {result.id}")
        click.echo("This will fetch/update all US locations from OpenAQ API")
        click.echo("⚠️  NOTE: This fetches LATEST data only, not historical data")

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
def fetch_page(page):
    """Manually trigger a single page of locations fetch"""
    with app.app_context():
        result = fetch_locations_page.delay(page, fetch_history=False)
        click.echo(f"Started locations page {page} task: {result.id}")
        click.echo(f"Fetching page {page} (latest data only)")

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
        
        # Count sensors with any data
        sensors_with_data = Sensor.query.filter(
            Sensor.last_value.is_not(None)
        ).count()
        
        # Get date range of all data
        date_range = db.session.query(
            db.func.min(Measurement.timestamp).label('oldest'),
            db.func.max(Measurement.timestamp).label('newest')
        ).first()
        
        click.echo("Current Data Status:")
        click.echo(f"  Total Locations: {total_locations}")
        click.echo(f"  Total Sensors: {total_sensors}")
        click.echo(f"  Sensors with Data: {sensors_with_data}")
        click.echo(f"  Total Measurements: {total_measurements}")
        
        if date_range.oldest and date_range.newest:
            click.echo(f"  Oldest Data: {date_range.oldest.strftime('%Y-%m-%d')}")
            click.echo(f"  Newest Data: {date_range.newest.strftime('%Y-%m-%d')}")
            data_span = (date_range.newest - date_range.oldest).days / 365.25
            click.echo(f"  Data Span: {data_span:.1f} years")
        
        if total_sensors > 0:
            data_percentage = (sensors_with_data / total_sensors * 100)
            click.echo(f"  Data Coverage: {data_percentage:.1f}%")

@cli.command()
def data_range():
    """Show data range for all locations"""
    with app.app_context():
        from app.models import Location, Sensor, Measurement
        
        # Get locations with data range
        locations_with_data = db.session.query(
            Location.id,
            Location.name,
            db.func.min(Measurement.timestamp).label('oldest'),
            db.func.max(Measurement.timestamp).label('newest'),
            db.func.count(Measurement.id).label('measurement_count')
        ).join(Sensor).join(Measurement).group_by(
            Location.id, Location.name
        ).order_by(db.func.min(Measurement.timestamp)).limit(20).all()
        
        click.echo("📊 Data Range for Top 20 Locations (by oldest data):")
        for loc in locations_with_data:
            span_years = (loc.newest - loc.oldest).days / 365.25
            click.echo(f"  {loc.name[:30]:30} | {loc.oldest.strftime('%Y-%m-%d')} to {loc.newest.strftime('%Y-%m-%d')} | {span_years:.1f} years | {loc.measurement_count} measurements")

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
            click.echo(f"Found {len(measurements)} latest measurements")
            
            if measurements:
                for measurement in measurements[:3]:  # Show first 3
                    param_name = measurement.get('parameter', {}).get('name', 'unknown')
                    value = measurement.get('value', 'N/A')
                    click.echo(f"  - {param_name}: {value}")
            else:
                click.echo("No measurements found")
                
        except Exception as e:
            click.echo(f"Error: {str(e)}")

if __name__ == '__main__':
    cli()
