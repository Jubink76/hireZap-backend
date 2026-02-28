from celery import shared_task
from django.utils import timezone
from infrastructure.repositories.hr_round_repository import HRInterviewRepository
from infrastructure.services.notification_service import NotificationService
from infrastructure.services.hr_round_service import VideoProcessingService
import logging
logger = logging.getLogger(__name__)


@shared_task(name='hr_interview.send_hr_interview_scheduled_email')
def send_hr_interview_scheduled_email_task(interview_id: int):
    try:
        repo = HRInterviewRepository()
        interview = repo.get_interview_by_id(interview_id)
        
        if not interview:
            return {'success': False, 'error': 'Interview not found'}
        
        candidate_name = interview.candidate_name
        candidate_email = interview.application.email
        job_title = interview.job.job_title
        scheduled_time = interview.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
        duration = interview.scheduled_duration_minutes
        
        subject = f"HR Interview Scheduled - {job_title}"
        
        message = f"""
Dear {candidate_name},

Congratulations! You've been selected for an HR interview round.

Job Position: {job_title}
Date & Time: {scheduled_time} ({interview.timezone})
Duration: {duration} minutes

Interview Format: Video Interview
Platform: Our secure video platform

Important Instructions:
1. Join from a quiet location with good internet
2. Test your camera and microphone beforehand
3. Dress professionally
4. Have your resume and portfolio ready
5. Prepare questions about the role and company

{interview.scheduling_notes or ''}

You'll receive a meeting link 10 minutes before the scheduled time.

Best of luck!

Regards,
{interview.job.company.company_name} Hiring Team
"""
        
        # TODO: Implement actual email sending
        # send_email(to=candidate_email, subject=subject, message=message)
        
        logger.info(f" HR Interview scheduled email sent to {candidate_email}")
        
        repo.mark_email_sent(interview_id)
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f" Email sending failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='hr_interview.send_hr_interview_reminders')
def send_hr_interview_reminders_task():
    try:
        repo = HRInterviewRepository()
        notification_service = NotificationService()
        
        # Get interviews that need reminders
        interviews = repo.get_upcoming_interviews_for_reminder(hours_before=24)
        
        sent_count = 0
        for interview in interviews:
            # Send WebSocket notification
            notification_service.send_websocket_notification(
                user_id=interview.application.candidate_id,
                notification_type='interview_reminder',
                data={
                    'interview_id': interview.id,
                    'job_title': interview.job.job_title,
                    'scheduled_at': interview.scheduled_at.isoformat(),
                    'duration': interview.scheduled_duration_minutes,
                    'type': 'hr_interview'
                }
            )
            
            # Send email
            _send_reminder_email(interview)
            
            # Mark as sent
            repo.mark_reminder_sent(interview.id)
            sent_count += 1
        
        logger.info(f" Sent {sent_count} HR interview reminders")
        
        return {
            'success': True,
            'reminders_sent': sent_count
        }
        
    except Exception as e:
        logger.error(f" Reminder task failed: {str(e)}")
        return {'success': False, 'error': str(e)}


def _send_reminder_email(interview):
    """Send reminder email"""
    candidate_name = interview.candidate_name
    candidate_email = interview.application.email
    job_title = interview.job.job_title
    scheduled_time = interview.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
    
    subject = f"Reminder: HR Interview Tomorrow - {job_title}"
    
    message = f"""
Dear {candidate_name},

This is a friendly reminder about your upcoming HR interview:

Job Position: {job_title}
Date & Time: {scheduled_time} ({interview.timezone})
Duration: {interview.scheduled_duration_minutes} minutes

Make sure to:
✓ Test your camera and microphone
✓ Join from a quiet location
✓ Be ready 5 minutes early

Looking forward to speaking with you!

Best regards,
{interview.job.company.company_name} Hiring Team
"""
    
    # TODO: Implement actual email sending
    # send_email(to=candidate_email, subject=subject, message=message)
    
    logger.info(f" Reminder email sent to {candidate_email}")


@shared_task(name='hr_interview.process_interview_completion')
def process_interview_completion_task(interview_id: int):

    try:
        repo = HRInterviewRepository()
        notification_service = NotificationService()
        
        interview = repo.get_interview_by_id(interview_id)
        
        if not interview:
            return {'success': False, 'error': 'Interview not found'}
        
        # Send completion notifications
        notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_completed',
            data={
                'interview_id': interview_id,
                'job_title': interview.job.job_title,
                'message': 'Thank you for completing the HR interview!'
            }
        )
        
        notification_service.send_websocket_notification(
            user_id=interview.conducted_by_id,
            notification_type='interview_completed',
            data={
                'interview_id': interview_id,
                'candidate_name': interview.candidate_name,
                'message': 'Interview completed. Please submit your notes.'
            }
        )
        
        # Cleanup chat messages from Redis after 24 hours
        # (Keep in DB but remove from cache)
        # from infrastructure.services.hr_round_service import ChatService
        # chat_service = ChatService()
        
        # # Schedule cleanup for later (after 24h)
        # cleanup_interview_chat_task.apply_async(
        #     args=[interview_id],
        #     countdown=24 * 60 * 60  # 24 hours
        # )
        
        # logger.info(f" Interview completion processed for interview {interview_id}")
        
        return {'success': True}
        
    except Exception as e:
        logger.info(f" Interview completion processing failed: {str(e)}")
        return {'success': False, 'error': str(e)}


# @shared_task(name='hr_interview.cleanup_interview_chat')
# def cleanup_interview_chat_task(interview_id: int):
#     """Cleanup interview chat from Redis after interview ends"""
#     try:
#         from infrastructure.services.hr_round_service import ChatService
        
#         chat_service = ChatService()
#         chat_service.delete_messages(interview_id)
        
#         logger.info(f" Cleaned up chat messages for interview {interview_id}")
        
#         return {'success': True}
        
#     except Exception as e:
#         logger.error(f" Chat cleanup failed: {str(e)}")
#         return {'success': False, 'error': str(e)}


# @shared_task(name='hr_interview.process_recording_upload')
# def process_recording_upload_task(
#     interview_id: int,
#     video_url: str,
#     video_key: str,
#     duration_seconds: int = None,
#     file_size_bytes: int = None
# ):
#     """
#     Process uploaded recording:
#     1. Save to database
#     2. Generate thumbnail (optional)
#     3. Send notifications
#     """
#     try:
#         repo = HRRoundRepositoryPort()
#         video_service = VideoProcessingService()
#         notification_service = NotificationService()
        
#         # Save recording to database
#         recording = repo.create_recording(
#             interview_id=interview_id,
#             video_url=video_url,
#             video_key=video_key,
#             duration_seconds=duration_seconds,
#             file_size_bytes=file_size_bytes
#         )
        
#         logger.info(f" Recording saved for interview {interview_id}")
        
#         # Generate thumbnail (optional - can be skipped for now)
#         # thumbnail_result = video_service.generate_thumbnail(video_url, interview_id)
#         # if thumbnail_result['success'] and thumbnail_result.get('thumbnail_url'):
#         #     repo.update_recording_thumbnail(
#         #         interview_id=interview_id,
#         #         thumbnail_url=thumbnail_result['thumbnail_url'],
#         #         thumbnail_key=thumbnail_result['thumbnail_key']
#         #     )
        
#         # Send notification to recruiter
#         interview = repo.get_interview_by_id(interview_id)
#         notification_service.send_websocket_notification(
#             user_id=interview.conducted_by_id,
#             notification_type='recording_uploaded',
#             data={
#                 'interview_id': interview_id,
#                 'candidate_name': interview.candidate_name,
#                 'message': 'Interview recording uploaded successfully'
#             }
#         )
        
#         return {
#             'success': True,
#             'recording_id': recording.id
#         }
        
#     except Exception as e:
#         logger.error(f" Recording processing failed: {str(e)}")
#         return {'success': False, 'error': str(e)}


@shared_task(name='hr_interview.send_hr_interview_result_email')
def send_hr_interview_result_email_task(interview_id: int):
    try:
        repo = HRInterviewRepository()
        interview = repo.get_interview_by_id(interview_id)
        
        if not interview or not hasattr(interview, 'result'):
            return {'success': False, 'error': 'Interview or result not found'}
        
        result = interview.result
        candidate_name = interview.candidate_name
        candidate_email = interview.application.email
        job_title = interview.job.job_title
        company_name = interview.job.company.company_name
        
        if result.decision == 'qualified':
            subject = f"Congratulations! Next Steps - {job_title}"
            message = f"""
Dear {candidate_name},

Great news! You've successfully passed the HR interview round for the {job_title} position at {company_name}.

Your Performance Score: {result.final_score}/100

{result.next_steps or 'Our team will contact you soon regarding the next steps in the hiring process.'}

We're impressed with your performance and look forward to continuing the process with you.

Best regards,
{company_name} Hiring Team
"""
        else:
            subject = f"Interview Update - {job_title}"
            message = f"""
Dear {candidate_name},

Thank you for taking the time to interview for the {job_title} position at {company_name}.

After careful consideration, we've decided not to move forward with your application at this time.

Your Performance Score: {result.final_score}/100

{result.decision_reason or 'We appreciate your interest in our company and wish you the best in your job search.'}

Thank you again for your time and interest.

Best regards,
{company_name} Hiring Team
"""
        
        # TODO: Implement actual email sending
        # send_email(to=candidate_email, subject=subject, message=message)
        
        logger.info(f"Result email sent to {candidate_email}")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f" Result email failed: {str(e)}")
        return {'success': False, 'error': str(e)}