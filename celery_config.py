"""
Celery Configuration for Multi-Tenant SQL Agent
Production-ready task queue with Redis broker
"""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Celery configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BROKER_URL = REDIS_URL
RESULT_BACKEND = REDIS_URL

# Create Celery instance
celery_app = Celery(
    'multitenant_sql_agent',
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        'celery_tasks',  # Import our task modules
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing and priorities
    task_routes={
        'celery_tasks.process_file_upload': {'queue': 'file_processing'},
        'celery_tasks.process_sql_query': {'queue': 'query_processing'},
        'celery_tasks.cleanup_user_session': {'queue': 'maintenance'},
    },
    
    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task time limits (in seconds)
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes hard limit
    
    # Task expiry
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-expired-sessions': {
            'task': 'celery_tasks.cleanup_expired_sessions',
            'schedule': 3600.0,  # Run every hour
        },
        'health-check': {
            'task': 'celery_tasks.health_check',
            'schedule': 300.0,  # Run every 5 minutes
        },
    },
)

# Define task queues
celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'file_processing': {
        'exchange': 'file_processing',
        'routing_key': 'file_processing',
    },
    'query_processing': {
        'exchange': 'query_processing', 
        'routing_key': 'query_processing',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance',
    },
}

if __name__ == '__main__':
    celery_app.start()
