"""
core/use_cases/telephonic_round/start_call_usecase.py
"""
from typing import Dict
import uuid
from django.utils import timezone
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService


class StartCallUseCase:
    """
    Start a telephonic interview call
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
        recruiter_id: int
    ) -> Dict:
        """
        Start interview call session
        
        Args:
            interview_id: Interview ID
            recruiter_id: ID of recruiter conducting the interview
        
        Returns:
            {
                'success': bool,
                'session_id': str,
                'interview_id': int,
                'candidate_id': int,
                'error': str (if failed)
            }
        """
        
        # 1. Get interview
        interview = self.repository.get_interview_by_id(interview_id)
        
        if not interview:
            return {
                'success': False,
                'error': 'Interview not found'
            }
        
        # 2. Validate interview status
        if interview.status not in ['scheduled', 'not_scheduled']:
            return {
                'success': False,
                'error': f'Interview cannot be started. Current status: {interview.status}'
            }
        
        # 3. Check if interview is scheduled and time is appropriate
        if interview.status == 'scheduled':
            now = timezone.now()
            scheduled_time = interview.scheduled_at
            
            # Allow starting 5 minutes before scheduled time
            from datetime import timedelta
            earliest_start = scheduled_time - timedelta(minutes=5)
            
            if now < earliest_start:
                return {
                    'success': False,
                    'error': 'Interview cannot be started yet. Please wait until scheduled time.'
                }
            
            # Allow starting up to 30 minutes after scheduled time
            latest_start = scheduled_time + timedelta(minutes=30)
            
            if now > latest_start:
                return {
                    'success': False,
                    'error': 'Interview scheduled time has passed. Please reschedule.'
                }
        
        # 4. Update interview status to in_progress
        interview = self.repository.update_interview_status(
            interview_id=interview_id,
            status='in_progress',
            started_at=timezone.now(),
            conducted_by_id=recruiter_id
        )
        
        # 5. Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # 6. Create call session
        call_session = self.repository.create_call_session(
            interview_id=interview_id,
            session_id=session_id,
            caller_id=str(recruiter_id),
            callee_id=str(interview.application.candidate_id)
        )
        
        # 7. Send WebSocket notification to candidate
        self._notify_candidate_call_started(interview, session_id)
        
        # 8. Send WebSocket notification to recruiter
        self._notify_recruiter_call_started(interview, session_id, recruiter_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'interview_id': interview_id,
            'candidate_id': interview.application.candidate_id,
            'candidate_name': f"{interview.application.first_name} {interview.application.last_name}",
            'job_title': interview.job.job_title,
            'message': 'Call started successfully'
        }
    
    def _notify_candidate_call_started(self, interview, session_id):
        """Notify candidate that call has started"""
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='call_started',
            data={
                'interview_id': interview.id,
                'session_id': session_id,
                'job_title': interview.job.job_title,
                'recruiter_name': interview.conducted_by.full_name if interview.conducted_by else 'Recruiter',
                'message': 'Your interview call has started'
            }
        )
    
    def _notify_recruiter_call_started(self, interview, session_id, recruiter_id):
        """Notify recruiter that call has started"""
        self.notification_service.send_websocket_notification(
            user_id=recruiter_id,
            notification_type='call_started',
            data={
                'interview_id': interview.id,
                'session_id': session_id,
                'candidate_name': f"{interview.application.first_name} {interview.application.last_name}",
                'job_title': interview.job.job_title,
                'message': 'Call connected'
            }
        )