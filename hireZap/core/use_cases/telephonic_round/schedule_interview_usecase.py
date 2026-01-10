from typing import Dict
from datetime import datetime
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService

class ScheduleInterviewUsecase:
    """Schedule telephonic interview"""
    def __init__(self, 
                 repository:TelephonicRoundRepositoryPort,
                 notification_service:NotificationService):
        self.repository = repository
        self.notification_service = notification_service

    def execute(self,
                application_id: int,
                scheduled_at: datetime,
                duration: int,
                timezone: str,
                notes: str = '',
                send_notification: bool = True,
                send_email: bool = True) -> Dict:
        
        # 1. Get or create interview record
        interview = self.repository.get_interview_by_application(application_id)
        
        if not interview:
            interview = self.repository.create_interview(
                application_id=application_id,
                status='not_scheduled'
            )
        
        # 2. Validate scheduled time is in future
        from django.utils import timezone as django_tz
        now = django_tz.now()
        if scheduled_at <= now:
            return {
                'success': False,
                'error': 'Scheduled time must be in the future'
            }
        
        # 3. Schedule the interview
        interview = self.repository.schedule_interview(
            interview_id=interview.id,
            scheduled_at=scheduled_at,
            duration=duration,
            timezone=timezone,
            notes=notes
        )
        
        # 4. Send notifications
        if send_notification:
            self._send_websocket_notification(interview)
            self.repository.update_interview_status(
                interview.id,
                interview.status,
                notification_sent=True
            )
        
        if send_email:
            self._send_email_notification(interview)
            self.repository.update_interview_status(
                interview.id,
                interview.status,
                email_sent=True
            )
        
        return {
            'success': True,
            'interview_id': interview.id,
            'scheduled_at': interview.scheduled_at.isoformat(),
            'duration': interview.scheduled_duration_minutes,
            'message': 'Interview scheduled successfully'
        }
    
    def _send_websocket_notification(self, interview):
        """Send WebSocket notification to candidate"""
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_scheduled',
            data={
                'interview_id': interview.id,
                'job_id': interview.job_id,
                'job_title': interview.job.job_title,
                'scheduled_at': interview.scheduled_at.isoformat(),
                'duration': interview.scheduled_duration_minutes,
                'timezone': interview.timezone,
                'notes': interview.scheduling_notes
            }
        )
    
    def _send_email_notification(self, interview):
        """Send email to candidate"""
        from telephonic_round.tasks import send_interview_scheduled_email_task
        
        send_interview_scheduled_email_task.delay(
            interview_id=interview.id
        )
