from typing import Dict, List
from django.utils import timezone
from datetime import timedelta
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService

class ScheduleInterviewUsecase:

    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.notification_service = NotificationService()
    def execute(
        self,
        application_id: int,
        scheduled_at: timezone.datetime,
        duration_minutes: int,
        timezone_str: str,
        conducted_by_id: int,
        scheduling_notes: str = None
    ) -> Dict:
        """
        Schedule HR interview for an application
        
        Returns:
            {
                'success': bool,
                'interview': HRInterview,
                'error': str (if failed)
            }
        """
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
            
            # Send notifications
            self._send_notifications(interview)
            
            # Send email (async via Celery)
            from hr_round.tasks import send_hr_interview_scheduled_email_task
            send_hr_interview_scheduled_email_task.delay(interview.id)
            
            print(f"✅ HR Interview scheduled for {interview.candidate_name} on {scheduled_at}")
            
            return {
                'success': True,
                'interview': interview
            }
            
        except Exception as e:
            print(f"❌ Schedule interview error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
    def _send_notifications(self, interview):
        """Send WebSocket notifications"""
        # To candidate
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_scheduled',
            data={
                'interview_id': interview.id,
                'type': 'hr_interview',
                'job_title': interview.job.job_title,
                'scheduled_at': interview.scheduled_at.isoformat(),
                'duration': interview.scheduled_duration_minutes,
                'message': f'HR Interview scheduled for {interview.job.job_title}'
            }
        )
        
        # To recruiter
        self.notification_service.send_websocket_notification(
            user_id=interview.conducted_by_id,
            notification_type='interview_scheduled',
            data={
                'interview_id': interview.id,
                'type': 'hr_interview',
                'candidate_name': interview.candidate_name,
                'scheduled_at': interview.scheduled_at.isoformat(),
                'message': f'Interview scheduled with {interview.candidate_name}'
            }
        )
        
        # Mark as sent
        self.repo.mark_notification_sent(interview.id)

class BulkScheduleHRInterviewUsecase:
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.schedule_use_case = ScheduleInterviewUsecase()

    def execute(
        self,
        application_ids: List[int],
        scheduled_at: timezone.datetime,
        duration_minutes: int,
        timezone_str: str,
        conducted_by_id: int,
        scheduling_notes: str = None,
        interval_minutes: int = 0  # Time gap between interviews
    ) -> Dict:
        """
        Schedule multiple HR interviews
        
        Args:
            interval_minutes: Time gap between each interview (for sequential scheduling)
        
        Returns:
            {
                'success': bool,
                'scheduled_count': int,
                'failed_count': int,
                'interviews': List[HRInterview],
                'errors': List[Dict]
            }
        """
        scheduled_interviews = []
        errors = []
        current_time = scheduled_at
        
        for index, app_id in enumerate(application_ids):
            # Calculate time for this interview
            if interval_minutes > 0 and index > 0:
                current_time = scheduled_at + timedelta(minutes=interval_minutes * index)
            
            result = self.schedule_use_case.execute(
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
        
        print(f"✅ Bulk scheduling complete: {len(scheduled_interviews)} scheduled, {len(errors)} failed")
        
        return {
            'success': len(errors) == 0,
            'scheduled_count': len(scheduled_interviews),
            'failed_count': len(errors),
            'interviews': scheduled_interviews,
            'errors': errors
        }
    
class RescheduleHRInterviewUsecase:
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.notification_service = NotificationService()

    def execute(
        self,
        interview_id: int,
        new_scheduled_at: timezone.datetime,
        new_duration_minutes: int = None,
        reschedule_reason: str = None
    ) -> Dict:
        """
        Reschedule HR interview
        
        Returns:
            {
                'success': bool,
                'interview': HRInterview,
                'error': str (if failed)
            }
        """
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
            
            # Send notifications
            self._send_reschedule_notifications(interview, old_time)
            
            # Send email
            from hr_round.tasks import send_hr_interview_scheduled_email_task
            send_hr_interview_scheduled_email_task.delay(interview.id)
            
            print(f"✅ Interview rescheduled from {old_time} to {new_scheduled_at}")
            
            return {
                'success': True,
                'interview': interview
            }
            
        except Exception as e:
            print(f"❌ Reschedule error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_reschedule_notifications(self, interview, old_time):
        """Send reschedule notifications"""
        # To candidate
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_rescheduled',
            data={
                'interview_id': interview.id,
                'type': 'hr_interview',
                'job_title': interview.job.job_title,
                'old_time': old_time.isoformat(),
                'new_time': interview.scheduled_at.isoformat(),
                'message': 'Your HR interview has been rescheduled'
            }
        )
        
        # To recruiter
        self.notification_service.send_websocket_notification(
            user_id=interview.conducted_by_id,
            notification_type='interview_rescheduled',
            data={
                'interview_id': interview.id,
                'candidate_name': interview.candidate_name,
                'old_time': old_time.isoformat(),
                'new_time': interview.scheduled_at.isoformat()
            }
        )

class CancelHRInterviewUsecase:
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.notification_service = NotificationService()

    def execute(
        self,
        interview_id: int,
        cancellation_reason: str,
        cancelled_by_id: int
    ) -> Dict:
        """
        Cancel HR interview
        
        Returns:
            {
                'success': bool,
                'interview': HRInterview,
                'error': str (if failed)
            }
        """
        try:
            interview = self.repo.cancel_interview(
                interview_id=interview_id,
                reason=cancellation_reason
            )
            
            # Send notifications
            self._send_cancellation_notifications(interview, cancelled_by_id)
            
            # Send email
            self._send_cancellation_email(interview)
            
            print(f"✅ Interview cancelled: {interview.candidate_name}")
            
            return {
                'success': True,
                'interview': interview
            }
            
        except Exception as e:
            print(f"❌ Cancel error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_cancellation_notifications(self, interview, cancelled_by_id):
        """Send cancellation notifications"""
        # To candidate
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_cancelled',
            data={
                'interview_id': interview.id,
                'type': 'hr_interview',
                'job_title': interview.job.job_title,
                'reason': interview.cancellation_reason,
                'message': 'Your HR interview has been cancelled'
            }
        )
        
        # To recruiter (if cancelled by someone else)
        if cancelled_by_id != interview.conducted_by_id:
            self.notification_service.send_websocket_notification(
                user_id=interview.conducted_by_id,
                notification_type='interview_cancelled',
                data={
                    'interview_id': interview.id,
                    'candidate_name': interview.candidate_name,
                    'reason': interview.cancellation_reason
                }
            )
    
    def _send_cancellation_email(self, interview):
        """Send cancellation email"""
        # TODO: Implement email sending
        pass