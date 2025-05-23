#!/usr/bin/env python
import click
from app import create_app
from app.tasks import fetch_latest_measurements_batch, fetch_all_locations, cleanup_old_measurements, fetch_all_measurements_orchestrator

app = create_app()

@click.group()
def cli():
    """Air Quality Management Commands"""
    pass

@cli.command()
def fetch_data():
    """Manually trigger latest measurements fetch for ALL locations"""
    with app.app_context():
        result = fetch_all_measurements_orchestrator.delay()
        click.echo(f"Started ALL locations measurements task: {result.id}")

@cli.command()
def update_locs():
    """Manually trigger location update for ALL 4,877 locations"""
    with app.app_context():
        result = fetch_all_locations.delay(fetch_history_pages=[1])
        click.echo(f"Started ALL 4,877 locations update task: {result.id}")

@cli.command()
def cleanup():
    """Manually trigger cleanup"""
    with app.app_context():
        result = cleanup_old_measurements.delay()
        click.echo(f"Started cleanup task: {result.id}")

@cli.command()
def fetch_all_data():
    """Fetch data from ALL locations with sensors"""
    with app.app_context():
        result = fetch_latest_measurements_batch.delay(batch_size=None)
        click.echo(f"Started ALL locations task: {result.id}")

if __name__ == '__main__':
    cli()
