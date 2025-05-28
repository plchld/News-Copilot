"""
Celery configuration for News Copilot project.
"""
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Create Celery app
app = Celery('news_copilot')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Celery Beat Schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'apps.news_aggregator.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}