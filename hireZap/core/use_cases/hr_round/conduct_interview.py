from typing import Dict
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService
from infrastructure.services.hr_round_service import MeetingService


class ConductInterviewUseCase:
    """Main use case for conducting interviews"""
    
    def __init__(self):
        self.start_use_case = StartMeetingUseCase()
        self.join_use_case = JoinMeetingUseCase()
        self.end_use_case = EndMeetingUseCase()
    
    def start_interview(self, interview_id: int, recruiter_id: int) -> Dict:
        """Start interview - delegates to StartMeetingUseCase"""
        return self.start_use_case.execute(interview_id, recruiter_id)
    
    def join_interview(self, session_id: str, participant_type: str) -> Dict:
        """Join interview - delegates to JoinMeetingUseCase"""
        return self.join_use_case.execute(session_id, participant_type)
    
    def end_interview(self, session_id: str, ended_by_id: int) -> Dict:
        """End interview - delegates to EndMeetingUseCase"""
        return self.end_use_case.execute(session_id, ended_by_id)
    
class StartMeetingUseCase:
    """Use case for starting a meeting"""
    
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.notification_service = NotificationService()
    
    def execute(self, interview_id: int, recruiter_id: int) -> Dict:
        """
        Start interview session
        
        Returns:
            {
                'success': bool,
                'session': MeetingSession,
                'interview': HRInterview,
                'error': str (if failed)
            }
        """
        try:
            interview = self.repo.get_interview_by_id(interview_id)
            
            if not interview:
                return {'success': False, 'error': 'Interview not found'}
            
            # Validate interview can be started
            if interview.status == 'completed':
                return {'success': False, 'error': 'Interview already completed'}
            
            if interview.status == 'cancelled':
                return {'success': False, 'error': 'Interview is cancelled'}
            
            # Validate recruiter
            if interview.conducted_by_id != recruiter_id:
                return {'success': False, 'error': 'Not authorized to start this interview'}
            
            # Check if session already exists
            existing_session = self.repo.get_meeting_session_by_interview(interview_id)
            if existing_session and not existing_session.ended_at:
                return {
                    'success': True,
                    'session': existing_session,
                    'interview': interview,
                    'message': 'Session already active'
                }
            
            # Create meeting session
            session = self.repo.create_meeting_session(
                interview_id=interview_id,
                recruiter_id=str(recruiter_id),
                candidate_id=str(interview.application.candidate_id)
            )
            
            # Update interview status
            self.repo.update_interview_status(interview_id, 'in_progress')
            
            # Send notification to candidate
            self.notification_service.send_websocket_notification(
                user_id=interview.application.candidate_id,
                notification_type='interview_started',
                data={
                    'interview_id': interview_id,
                    'session_id': session.session_id,
                    'room_id': session.room_id,
                    'job_title': interview.job.job_title,
                    'message': 'Your HR interview is ready to join'
                }
            )
            
            print(f"✅ Meeting started: {session.session_id}")
            
            return {
                'success': True,
                'session': session,
                'interview': interview
            }
            
        except Exception as e:
            print(f"❌ Start meeting error: {str(e)}")
            return {'success': False, 'error': str(e)}


class JoinMeetingUseCase:
    """Use case for joining a meeting"""
    
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.notification_service = NotificationService()
        self.meeting_service = MeetingService()
    
    def execute(self, session_id: str, participant_type: str, user_id: int = None) -> Dict:
        """
        Participant joins interview
        
        Args:
            session_id: Meeting session ID
            participant_type: 'recruiter' or 'candidate'
            user_id: User ID (for validation)
        
        Returns:
            {
                'success': bool,
                'session': MeetingSession,
                'error': str (if failed)
            }
        """
        try:
            session = self.repo.get_meeting_session(session_id)
            
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            # Validate session is active
            if session.ended_at:
                return {'success': False, 'error': 'Session has ended'}
            
            # Validate participant access (optional)
            if user_id:
                access_result = self.meeting_service.validate_meeting_access(
                    interview_id=session.interview.id,
                    user_id=user_id,
                    user_type=participant_type
                )
                if not access_result['allowed']:
                    return {'success': False, 'error': access_result['reason']}
            
            # Update connection status
            self.repo.update_participant_connection(
                session_id=session_id,
                participant_type=participant_type,
                connected=True
            )
            
            # Send notification when candidate joins
            if participant_type == 'candidate':
                self.notification_service.send_websocket_notification(
                    user_id=int(session.recruiter_id),
                    notification_type='candidate_joined',
                    data={
                        'interview_id': session.interview.id,
                        'candidate_name': session.interview.candidate_name,
                        'session_id': session_id,
                        'message': f'{session.interview.candidate_name} has joined the interview'
                    }
                )
            
            print(f"✅ {participant_type} joined meeting: {session_id}")
            
            return {'success': True, 'session': session}
            
        except Exception as e:
            print(f"❌ Join meeting error: {str(e)}")
            return {'success': False, 'error': str(e)}


class EndMeetingUseCase:
    """Use case for ending a meeting"""
    
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.notification_service = NotificationService()
    
    def execute(self, session_id: str, ended_by_id: int = None) -> Dict:
        """
        End interview session
        
        Returns:
            {
                'success': bool,
                'session': MeetingSession,
                'error': str (if failed)
            }
        """
        try:
            session = self.repo.end_meeting_session(session_id)
            
            # Send notifications to both parties
            self.notification_service.send_websocket_notification(
                user_id=int(session.recruiter_id),
                notification_type='interview_ended',
                data={
                    'interview_id': session.interview.id,
                    'session_id': session_id,
                    'candidate_name': session.interview.candidate_name,
                    'message': 'Interview session ended'
                }
            )
            
            self.notification_service.send_websocket_notification(
                user_id=int(session.candidate_id),
                notification_type='interview_ended',
                data={
                    'interview_id': session.interview.id,
                    'session_id': session_id,
                    'message': 'Interview session ended. Thank you for your time!'
                }
            )
            
            # Trigger post-interview tasks
            from hr_round.tasks import process_interview_completion_task
            process_interview_completion_task.delay(session.interview.id)
            
            print(f"✅ Meeting ended: {session_id}")
            
            return {'success': True, 'session': session}
            
        except Exception as e:
            print(f"❌ End meeting error: {str(e)}")
            return {'success': False, 'error': str(e)}