"""
core/use_cases/telephonic_round/reschedule_interview_usecase.py
"""
from typing import Dict, Optional
from datetime import datetime
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService


class RescheduleInterviewUseCase:
    """
    Reschedule an existing interview
    """
    
    def __init__(
        self,
        repository: TelephonicRoundRepositoryPort,
        notification_service: NotificationService
    ):
        self.repository = repository
        self.notification_service = notification_service
    
    def execute(
        self,
        interview_id: int,
        new_scheduled_at: datetime,
        duration: Optional[int] = None,
        timezone: Optional[str] = None,
        notes: Optional[str] = None,
        send_notification: bool = True,
        send_email: bool = True
    ) -> Dict:
        """
        Reschedule interview
        
        Args:
            interview_id: Interview ID
            new_scheduled_at: New scheduled datetime
            duration: New duration (optional, keeps existing if not provided)
            timezone: New timezone (optional, keeps existing if not provided)
            notes: New notes (optional, appends to existing)
            send_notification: Whether to send notification
            send_email: Whether to send email
        """
        
        # 1. Get existing interview
        interview = self.repository.get_interview_by_id(interview_id)
        
        if not interview:
            return {
                'success': False,
                'error': 'Interview not found'
            }
        
        # 2. Validate interview can be rescheduled
        if interview.status not in ['scheduled', 'not_scheduled']:
            return {
                'success': False,
                'error': f'Interview cannot be rescheduled. Current status: {interview.status}'
            }
        
        # 3. Validate new scheduled time is in future
        from django.utils import timezone as django_tz
        now = django_tz.now()
        
        if new_scheduled_at <= now:
            return {
                'success': False,
                'error': 'Scheduled time must be in the future'
            }
        
        # 4. Store old schedule for notification
        old_scheduled_at = interview.scheduled_at
        
        # 5. Prepare update data
        update_duration = duration if duration is not None else interview.scheduled_duration_minutes
        update_timezone = timezone if timezone is not None else interview.timezone
        
        # Handle notes - append or replace
        if notes:
            if interview.scheduling_notes:
                update_notes = f"{interview.scheduling_notes}\n\nRescheduled: {notes}"
            else:
                update_notes = notes
        else:
            update_notes = interview.scheduling_notes
        
        # 6. Reschedule the interview
        interview = self.repository.schedule_interview(
            interview_id=interview_id,
            scheduled_at=new_scheduled_at,
            duration=update_duration,
            timezone=update_timezone,
            notes=update_notes
        )
        
        # Reset reminder flag so it can be sent again
        self.repository.update_interview_status(
            interview_id=interview_id,
            status='scheduled',
            reminder_sent=False
        )
        
        # 7. Send notifications
        if send_notification:
            self._send_reschedule_notification(
                interview=interview,
                old_scheduled_at=old_scheduled_at
            )
        
        if send_email:
            self._send_reschedule_email(
                interview=interview,
                old_scheduled_at=old_scheduled_at
            )
        
        return {
            'success': True,
            'interview_id': interview_id,
            'old_scheduled_at': old_scheduled_at.isoformat() if old_scheduled_at else None,
            'new_scheduled_at': interview.scheduled_at.isoformat(),
            'duration': interview.scheduled_duration_minutes,
            'timezone': interview.timezone,
            'message': 'Interview rescheduled successfully'
        }
    
    def _send_reschedule_notification(self, interview, old_scheduled_at):
        """Send WebSocket notification about rescheduling"""
        
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_rescheduled',
            data={
                'interview_id': interview.id,
                'job_id': interview.job_id,
                'job_title': interview.job.job_title,
                'old_scheduled_at': old_scheduled_at.isoformat() if old_scheduled_at else None,
                'new_scheduled_at': interview.scheduled_at.isoformat(),
                'duration': interview.scheduled_duration_minutes,
                'timezone': interview.timezone,
                'notes': interview.scheduling_notes,
                'message': 'Your interview has been rescheduled'
            }
        )
    
    def _send_reschedule_email(self, interview, old_scheduled_at):
        """Send email about rescheduling"""
        from telephonic_round.tasks import send_interview_rescheduled_email_task
        
        send_interview_rescheduled_email_task.apply_async(
            args=[interview.id, old_scheduled_at.isoformat() if old_scheduled_at else None],
            countdown=2
        )