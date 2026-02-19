from typing import Dict, List
from django.utils import timezone
from datetime import timedelta
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

class ScheduleInterviewUsecase:

    def __init__(self, 
                 repository: HRRoundRepositoryPort, 
                 notification_service: NotificationService):
        self.repo = repository  
        self.notification_service = notification_service
        
    def execute(
        self,
        application_id: int,
        scheduled_at: timezone.datetime,
        duration_minutes: int,
        timezone_str: str,
        conducted_by_id: int,
        scheduling_notes: str = None) -> Dict:
        try:
            # Validate scheduled time (must be in future)
            if scheduled_at <= timezone.now():
                return {
                    'success': False,
                    'error': 'Scheduled time must be in the future'
                }
            
            # Schedule interview
            interview = self.repo.schedule_interview(
                application_id=application_id,
                scheduled_at=scheduled_at,
                duration_minutes=duration_minutes,
                timezone_str=timezone_str,
                conducted_by_id=conducted_by_id,
                scheduling_notes=scheduling_notes
            )
            
            self._send_notifications(interview)
            
            # Send email (async via Celery)
            from hr_round.tasks import send_hr_interview_scheduled_email_task
            send_hr_interview_scheduled_email_task.delay(interview.id)
            
            logger.info(f" HR Interview scheduled for {interview.candidate_name} on {scheduled_at}")
            
            return {
                'success': True,
                'interview': interview,
                'message': 'Interview scheduled successfully'
            }
            
        except Exception as e:
            logger.error(f" Schedule interview error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
    def _send_notifications(self, interview):
        """Send WebSocket notifications via Channels"""
        channel_layer = get_channel_layer()
        
        #Send to candidate
        async_to_sync(channel_layer.group_send)(
            f'user_{interview.application.candidate_id}',
            {
                'type': 'hr_interview_scheduled', 
                'message': f'Your HR interview for {interview.job.job_title} has been scheduled',
                'data': {
                    'interview_id': interview.id,
                    'interview_type': 'hr_video',
                    'job_title': interview.job.job_title,
                    'company_name': interview.job.company.company_name,
                    'scheduled_at': interview.scheduled_at.isoformat(),
                    'duration_minutes': interview.scheduled_duration_minutes,
                    'timezone': interview.timezone,
                    'application_id': interview.application_id,
                }
            }
        )
        
        logger.info(f"WebSocket notification sent to candidate {interview.application.candidate_id}")
        
        # ✅ Send to recruiter
        async_to_sync(channel_layer.group_send)(
            f'user_{interview.conducted_by_id}',
            {
                'type': 'hr_interview_scheduled', 
                'message': f'Interview scheduled with {interview.candidate_name}',
                'data': {
                    'interview_id': interview.id,
                    'interview_type': 'hr_video',
                    'candidate_name': interview.candidate_name,
                    'scheduled_at': interview.scheduled_at.isoformat(),
                    'duration_minutes': interview.scheduled_duration_minutes,
                }
            }
        )
        
        logger.info(f"WebSocket notification sent to recruiter {interview.conducted_by_id}")
        
        # Mark as sent in database
        try:
            self.repo.mark_notification_sent(interview.id)
        except Exception as e:
            logger.warning(f"Failed to mark notification as sent: {e}")


class BulkScheduleHRInterviewUsecase:
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        notification_service: NotificationService):
        
        self.repo = repository
        self.notification_service = notification_service

    def execute(
        self,
        application_ids: List[int],
        scheduled_at: timezone.datetime,
        duration_minutes: int,
        timezone_str: str,
        conducted_by_id: int,
        scheduling_notes: str = None,
        interval_minutes: int = 0) -> Dict:

        scheduled_interviews = []
        errors = []
        current_time = scheduled_at
        
        for index, app_id in enumerate(application_ids):
            # Calculate time for this interview
            if interval_minutes > 0 and index > 0:
                current_time = scheduled_at + timedelta(minutes=interval_minutes * index)
            
            # Create ScheduleInterviewUsecase for each interview
            schedule_use_case = ScheduleInterviewUsecase(
                repository=self.repo,
                notification_service=self.notification_service
            )
            
            result = schedule_use_case.execute(
                application_id=app_id,
                scheduled_at=current_time,
                duration_minutes=duration_minutes,
                timezone_str=timezone_str,
                conducted_by_id=conducted_by_id,
                scheduling_notes=scheduling_notes
            )
            
            if result['success']:
                scheduled_interviews.append(result['interview'])
            else:
                errors.append({
                    'application_id': app_id,
                    'error': result['error']
                })
        
        logger.info(f"✅ Bulk scheduling complete: {len(scheduled_interviews)} scheduled, {len(errors)} failed")
        
        return {
            'success': len(errors) == 0,
            'scheduled_count': len(scheduled_interviews),
            'failed_count': len(errors),
            'interviews': scheduled_interviews,
            'errors': errors,
            'message': f'{len(scheduled_interviews)} interviews scheduled successfully'
        }
    
class RescheduleHRInterviewUsecase:
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        notification_service: NotificationService):
        
        self.repo = repository
        self.notification_service = notification_service

    def execute(
        self,
        interview_id: int,
        new_scheduled_at: timezone.datetime,
        new_duration_minutes: int = None,
        reschedule_reason: str = None) -> Dict:
        
        try:
            interview = self.repo.get_interview_by_id(interview_id)
            
            if not interview:
                return {'success': False, 'error': 'Interview not found'}
            
            # Validate new time
            if new_scheduled_at <= timezone.now():
                return {
                    'success': False,
                    'error': 'New scheduled time must be in the future'
                }
            
            # Check if interview can be rescheduled
            if interview.status not in ['not_scheduled', 'scheduled']:
                return {
                    'success': False,
                    'error': f'Cannot reschedule interview with status: {interview.status}'
                }
            
            # Update interview
            old_time = interview.scheduled_at
            interview.scheduled_at = new_scheduled_at
            if new_duration_minutes:
                interview.scheduled_duration_minutes = new_duration_minutes
            if reschedule_reason:
                interview.scheduling_notes = f"Rescheduled: {reschedule_reason}\n{interview.scheduling_notes or ''}"
            interview.reminder_sent = False  # Reset reminder
            interview.save()
            
            self._send_reschedule_notifications(interview, old_time)
            
            # Send email
            from hr_round.tasks import send_hr_interview_scheduled_email_task
            send_hr_interview_scheduled_email_task.delay(interview.id)
            
            logger.info(f"✅ Interview rescheduled from {old_time} to {new_scheduled_at}")
            
            return {
                'success': True,
                'interview': interview,
                'message': 'Interview rescheduled successfully'
            }
            
        except Exception as e:
            logger.error(f"Reschedule error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_reschedule_notifications(self, interview, old_time):
        """Send reschedule notifications via Channels"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'user_{interview.application.candidate_id}',
            {
                'type': 'hr_interview_rescheduled', 
                'message': f'Your HR interview has been rescheduled',
                'data': {
                    'interview_id': interview.id,
                    'interview_type': 'hr_video',
                    'job_title': interview.job.job_title,
                    'old_time': old_time.isoformat(),
                    'new_time': interview.scheduled_at.isoformat(),
                    'duration_minutes': interview.scheduled_duration_minutes,
                }
            }
        )
        
        # To recruiter
        async_to_sync(channel_layer.group_send)(
            f'user_{interview.conducted_by_id}',
            {
                'type': 'hr_interview_rescheduled', 
                'message': f'Interview with {interview.candidate_name} rescheduled',
                'data': {
                    'interview_id': interview.id,
                    'candidate_name': interview.candidate_name,
                    'old_time': old_time.isoformat(),
                    'new_time': interview.scheduled_at.isoformat(),
                }
            }
        )

class CancelHRInterviewUsecase:
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        notification_service: NotificationService):
        
        self.repo = repository
        self.notification_service = notification_service

    def execute(
        self,
        interview_id: int,
        cancellation_reason: str,
        cancelled_by_id: int) -> Dict:
        try:
            interview = self.repo.cancel_interview(
                interview_id=interview_id,
                reason=cancellation_reason
            )
            
            self._send_cancellation_notifications(interview, cancelled_by_id)
            
            # Send email
            self._send_cancellation_email(interview)
            
            logger.info(f"✅ Interview cancelled: {interview.candidate_name}")
            
            return {
                'success': True,
                'interview': interview,
                'message': 'Interview cancelled successfully'
            }
            
        except Exception as e:
            logger.error(f" Cancel error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_cancellation_notifications(self, interview, cancelled_by_id):
        """Send cancellation notifications via Channels"""
        channel_layer = get_channel_layer()
        
        # To candidate
        async_to_sync(channel_layer.group_send)(
            f'user_{interview.application.candidate_id}',
            {
                'type': 'hr_interview_cancelled',
                'message': 'Your HR interview has been cancelled',
                'data': {
                    'interview_id': interview.id,
                    'interview_type': 'hr_video',
                    'job_title': interview.job.job_title,
                    'reason': interview.cancellation_reason,
                }
            }
        )
        
        # To recruiter (if cancelled by someone else)
        if cancelled_by_id != interview.conducted_by_id:
            async_to_sync(channel_layer.group_send)(
                f'user_{interview.conducted_by_id}',
                {
                    'type': 'hr_interview_cancelled', 
                    'message': f'Interview with {interview.candidate_name} cancelled',
                    'data': {
                        'interview_id': interview.id,
                        'candidate_name': interview.candidate_name,
                        'reason': interview.cancellation_reason,
                    }
                }
            )
    
    def _send_cancellation_email(self, interview):
        """Send cancellation email via Celery"""
        # TODO: Implement cancellation email task
        pass