import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hireZap.settings')
app = Celery('hireZap')
app.config_from_object('django.conf:settings',namespace='CELERY')
app.autodiscover_tasks()
