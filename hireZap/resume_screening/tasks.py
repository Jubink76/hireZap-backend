from celery import shared_task
from infrastructure.repositories.resume_screening_repository import ResumeScreeningRepository
from infrastructure.repositories.ats_configuration_repository import ATSConfigRepository
from infrastructure.services.notification_service import NotificationService
from core.use_cases.resume_screening.screen_single_resume_usecase import ScreenResumeUseCase


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={'max_retries': 3}
)
def screen_single_resume(self, application_id: int):
    """
    Screen a single resume (THIN - delegates to use case)
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 Starting screening for application {application_id}")
        # Initialize dependencies
        screening_repo = ResumeScreeningRepository()
        ats_repo = ATSConfigRepository()
        notification_service = NotificationService()
        
        # Execute use case
        use_case = ScreenResumeUseCase(screening_repo, ats_repo, notification_service)
        result = use_case.execute(application_id)
        
        if result['success']:
            logger.info(f"✅ Screening completed for application {application_id}: {result['decision']}")
        else:
            logger.error(f"❌ Screening failed for application {application_id}: {result.get('error')}")
        return result
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Exception screening application {application_id}: {str(e)}")
        logger.error(traceback.format_exc())
        # Mark as failed
        screening_repo = ResumeScreeningRepository()
        screening_repo.mark_screening_as_failed(
            application_id=application_id,
            error=str(e),
            retry_count=self.request.retries
        )
        
        # Re-raise for Celery retry
        raise


@shared_task
def start_bulk_screening(job_id: int):
    """
    Start bulk screening (THIN - delegates to repository)
    """
    try:
        import logging
        logger = logging.getLogger(__name__)

        screening_repo = ResumeScreeningRepository()
        notification_service = NotificationService()
        
        # Get job
        job = screening_repo.get_job_by_id(job_id)
        if not job:
            logger.error(f"❌ Job {job_id} not found")
            return {
                'success': False,
                'error': f'Job {job_id} not found'
            }
        
        # Get pending applications
        application_ids = screening_repo.get_pending_applications_by_job(job_id)
        
        logger.info(f"📊 Found {len(application_ids)} pending applications")
        if not application_ids:
            return {
                'success': False,
                'error': 'No pending applications to screen'
            }
        
        # Update job status
        screening_repo.update_job_screening_status(
            job_id=job_id,
            status='in_progress',
            total_applications_count=len(application_ids),
            screened_applications_count=0
        )
        logger.info(f"✅ Job status updated to 'in_progress'")
        # Dispatch individual tasks
        task_ids = []
        for app_id in application_ids:
            task = screen_single_resume.delay(app_id)
            task_ids.append(task.id)
        logger.info(f"✅ Dispatched {len(task_ids)} screening tasks")
        # Send notification
        notification_service.send_websocket_notification(
            user_id=job.recruiter.id,
            notification_type='bulk_screening_started',
            data={
                'job_id': job.id,
                'job_title': job.job_title,
                'total_applications': len(application_ids),
            }
        )
        
        return {
            'success': True,
            'job_id': job_id,
            'total_applications': len(application_ids),
            'task_ids': task_ids
        }
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Bulk screening failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def check_screening_completion(job_id: int):
    """
    Check if screening is complete (THIN)
    """
    try:
        screening_repo = ResumeScreeningRepository()
        notification_service = NotificationService()
        
        job = screening_repo.get_job_by_id(job_id)
        if not job or job.screening_status != 'in_progress':
            return
        
        # Check if all complete
        if screening_repo.check_all_screening_complete(job_id):
            # Mark as completed
            screening_repo.update_job_screening_status(job_id, 'completed')
            
            # Send notification
            notification_service.send_websocket_notification(
                user_id=job.recruiter.id,
                notification_type='bulk_screening_completed',
                data={
                    'job_id': job.id,
                    'job_title': job.job_title,
                    'total_screened': job.screened_applications_count,
                }
            )
            
    except Exception as e:
        print(f"Error checking screening completion: {str(e)}")


# ========== EMAIL TASKS ==========

@shared_task
def send_screening_result_email_task(
    application_id: int,
    decision: str,
    score: int
):
    """Send screening result email (THIN)"""
    try:
        from application.models import ApplicationModel
        from infrastructure.email.email_sender import EmailSender
        
        application = ApplicationModel.objects.select_related(
            'candidate__user',
            'job__company',
            'screening_result'
        ).get(id=application_id)

        candidate_name = f"{application.first_name} {application.last_name}".strip()
        if not candidate_name:
            # Fallback to user name
            candidate_name = f"{application.candidate.user.first_name} {application.candidate.user.last_name}".strip()
        if not candidate_name:
            candidate_name = "Candidate"
        
        # Get AI summary
        summary = ""
        try:
            summary = application.screening_result.ai_summary
        except:
            pass
        
        # Build email
        if decision == 'qualified':
            subject = f"Good News! Resume Screening Passed - {application.job.job_title}"
            body = f"""
Dear {candidate_name},

Congratulations! Your resume has been successfully screened for {application.job.job_title} at {application.job.company.company_name}.

📊 Score: {score}/100 - ✅ Qualified

{f"Summary: {summary}" if summary else ""}

Our team will contact you soon.

Best regards,
{application.job.company.company_name}
            """
        else:
            subject = f"Application Update - {application.job.job_title}"
            body = f"""
Dear {candidate_name},

Thank you for applying. After review, we will not be moving forward at this time.

📊 Score: {score}/100

{f"Feedback: {summary}" if summary else ""}

Best regards,
{application.job.company.company_name}
            """
        
        EmailSender().send_email(application.email, subject, body)
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def send_stage_progress_email_task(
    application_id: int,
    current_stage: str,
    next_stage: str
):
    """Send stage progression email (THIN)"""
    try:
        from application.models import ApplicationModel
        from infrastructure.email.email_sender import EmailSender
        
        application = ApplicationModel.objects.select_related(
            'candidate__user',
            'job__company'
        ).get(id=application_id)

        candidate_name = f"{application.first_name} {application.last_name}".strip()
        if not candidate_name:
            # Fallback to user name
            candidate_name = f"{application.candidate.user.first_name} {application.candidate.user.last_name}".strip()
        if not candidate_name:
            candidate_name = "Candidate"
        
        subject = f"🎉 Moving to {next_stage} - {application.job.job_title}"
        body = f"""
Dear {candidate_name},

Congratulations! You've completed {current_stage} and are moving to {next_stage}.

We'll contact you soon.

Best regards,
{application.job.company.company_name}
        """
        
        EmailSender().send_email(application.email, subject, body)
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}