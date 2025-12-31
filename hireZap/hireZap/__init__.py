from .celery import app as celery_app

__all__ = ('celery_app',)
# this ensures celery loads django settings, tasks auto register