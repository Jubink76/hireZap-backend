from typing import Dict
from django.utils import timezone
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService

class JoinCallUsecase:
    def __init__(
            self,
            repository:TelephonicRoundRepositoryPort,
            notification_service:NotificationService):
        self.repository = repository
        self.notification_service = notification_service
    

    def execute(self, interview_id:int, candidate_id:int) ->Dict:

        # get interview
        interview = self.repository.get_interview_by_id(interview_id)
        if not interview:
            return {
                'success': False,
                'error': 'Interview not found'
            }
        
        # verify candiate owns this interview
        if interview.application.candidate_id != candidate_id:
            return {
                'success': False,
                'error': 'Unauthorized: This interview does not belong to you'
            }
        # validate interview status
        if interview.status != 'in_progress':
            return {
                'success': False,
                'error': f'Interview is not ready to join. Current status: {interview.status}'
            }
        # get active call sessions
        active_session = interview.call_session
        if not active_session:
            return {
                'success': False,
                'error': 'No active call session found'
            }
        # update interview status
        interview = self.repository.update_interview_status(
            interview_id=interview_id,
            status='joined'
        )
        # update call session with candiate join time
        self.repository.update_call_session(
            session_id=active_session.session_id,
            candidate_joined_at=timezone.now()
        )
        #Notify recruiter that candidate joined
        self._notify_recruiter_candidate_joined(interview, candidate_id)
        
        return {
            'success': True,
            'session_id': active_session.session_id,
            'interview_id': interview_id,
            'recruiter_name': interview.conducted_by.full_name if interview.conducted_by else 'Recruiter',
            'job_title': interview.job.job_title,
            'message': 'Successfully joined the interview'
        }
    
    def _notify_recruiter_candidate_joined(self, interview, candidate_id):
        """Notify recruiter that candidate has joined"""
        self.notification_service.send_websocket_notification(
            user_id=interview.conducted_by_id,
            notification_type='candidate_joined',
            data={
                'interview_id': interview.id,
                'candidate_name': f"{interview.application.first_name} {interview.application.last_name}",
                'candidate_id': candidate_id,
                'message': 'Candidate has joined the interview'
            }
        )