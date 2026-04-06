import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hireZap.settings')
app = Celery('hireZap')
app.config_from_object('django.conf:settings',namespace='CELERY')
app.conf.beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler'
app.autodiscover_tasks()

# celery -A hireZap worker -P solo -l INFO
# celery -A hireZap beat -l info
# celery -A hireZap beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
