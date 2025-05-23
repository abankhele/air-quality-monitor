from celery import Celery
from app import create_app
import os

def make_celery():
    """Create and configure Celery instance with proper Flask integration"""
    app = create_app()
    
    celery = Celery(
        app.import_name,
        broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        include=['app.tasks']
    )
    
    # Update configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,
        task_soft_time_limit=25 * 60,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
    )
    
    # CRITICAL: Make celery work with Flask app context
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Create the celery instance
celery = make_celery()

if __name__ == '__main__':
    celery.start()
