"""
core/use_cases/telephonic_round/bulk_schedule_usecase.py
"""
from typing import Dict, List
from datetime import datetime
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService


class BulkScheduleUseCase:
    """
    Bulk schedule multiple interviews at once
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
        schedules: List[Dict],
        send_notifications: bool = True,
        send_emails: bool = True
    ) -> Dict:
        """
        Bulk schedule interviews
        
        Args:
            schedules: List of schedule data
            [
                {
                    'application_id': 1,
                    'scheduled_at': datetime,
                    'duration': 30,
                    'timezone': 'America/New_York',
                    'notes': ''
                },
                ...
            ]
        """
        
        scheduled_count = 0
        failed_count = 0
        errors = []
        
        for schedule_data in schedules:
            try:
                # 1. Get or create interview record
                application_id = schedule_data['application_id']
                interview = self.repository.get_interview_by_application(application_id)
                
                if not interview:
                    interview = self.repository.create_interview(
                        application_id=application_id,
                        status='not_scheduled'
                    )
                
                # 2. Validate scheduled time
                scheduled_at = schedule_data['scheduled_at']
                from django.utils import timezone as django_tz
                now = django_tz.now()
                
                if scheduled_at <= now:
                    errors.append({
                        'application_id': application_id,
                        'error': 'Scheduled time must be in the future'
                    })
                    failed_count += 1
                    continue
                
                # 3. Schedule the interview
                interview = self.repository.schedule_interview(
                    interview_id=interview.id,
                    scheduled_at=scheduled_at,
                    duration=schedule_data.get('duration', 30),
                    timezone=schedule_data.get('timezone', 'America/New_York'),
                    notes=schedule_data.get('notes', '')
                )
                
                # 4. Send notifications
                if send_notifications:
                    self._send_websocket_notification(interview)
                    self.repository.update_interview_status(
                        interview.id,
                        interview.status,
                        notification_sent=True
                    )
                
                if send_emails:
                    self._send_email_notification(interview)
                    self.repository.update_interview_status(
                        interview.id,
                        interview.status,
                        email_sent=True
                    )
                
                scheduled_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append({
                    'application_id': schedule_data.get('application_id'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'scheduled_count': scheduled_count,
            'failed_count': failed_count,
            'total': len(schedules),
            'errors': errors,
            'message': f'Successfully scheduled {scheduled_count} out of {len(schedules)} interviews'
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