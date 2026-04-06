from celery import shared_task
from django.utils import timezone
from job.models import JobModel
import logging
logger = logging.getLogger(__name__)

@shared_task(name='jobs.expire_deadline_passed_jobs')
def expire_deadline_passed_jobs():
    now = timezone.now()

    expired = JobModel.objects.filter(
        status = 'active',
        application_deadline__lt = now,
        application_deadline__isnull=False,
    )
    count = expired.count()
    expired.update(status='expired', update_at=now)

    logger.info(f"[Celery Beat] Expired {count} job(s) past their deadline.")
    return {'expired_count': count}
