from celery import Celery
import os

# Celery configuration
celery_app = Celery(
    'kyc_worker',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    include=['worker.tasks']
)

# Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'worker.tasks.process_kyc_video': {'queue': 'kyc_processing'},
    },
)