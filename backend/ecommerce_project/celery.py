"""
Celery configuration for ecommerce_project.
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

app = Celery('ecommerce_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Import and configure periodic tasks
from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES, CELERY_TASK_QUEUES

app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
app.conf.task_routes = CELERY_TASK_ROUTES
app.conf.task_create_missing_queues = True

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')