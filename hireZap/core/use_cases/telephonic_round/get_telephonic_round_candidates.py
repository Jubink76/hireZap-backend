from typing import Dict, Optional
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort

class GetTelephonicRoundCandidates():
    def __init__(self,repository:TelephonicRoundRepositoryPort):
        self.repository =repository
    
    def execute(self,job_id:int,  status_filter:Optional[str] = None):

        try:
            # Get all interviews for the job
            interviews = self.repository.get_interviews_by_job(job_id, status=status_filter)
            
            # Serialize interviews
            candidates = [self._serialize_interview(interview) for interview in interviews]
            
            # Get statistics
            stats = self.repository.get_job_interview_stats(job_id)
            
            return {
                'success': True,
                'candidates': candidates,
                'total': len(candidates),
                'stats': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to fetch candidates: {str(e)}'
            }
    
    def _serialize_interview(self, interview) -> Dict:
        """Convert interview model to dictionary"""
        return {
            'interview_id': interview.id,
            'application_id': interview.application_id,
            'candidate': {
                'id': interview.application.candidate_id,
                'name': f"{interview.application.first_name} {interview.application.last_name}",
                'email': interview.application.email,
                'phone': getattr(interview.application, 'phone', None),
            },
            'status': interview.status,
            'scheduled_at': interview.scheduled_at.isoformat() if interview.scheduled_at else None,
            'duration': interview.scheduled_duration_minutes,
            'timezone': interview.timezone,
            'started_at': interview.started_at.isoformat() if interview.started_at else None,
            'ended_at': interview.ended_at.isoformat() if interview.ended_at else None,
            'actual_duration_seconds': interview.actual_duration_seconds,
            'has_recording': bool(hasattr(interview, 'call_session') and 
                                 interview.call_session and 
                                 interview.call_session.recording_url),
            'has_transcription': bool(hasattr(interview, 'transcription') and interview.transcription),
            'has_results': bool(hasattr(interview, 'performance_result') and interview.performance_result),
            'overall_score': (interview.performance_result.overall_score 
                            if hasattr(interview, 'performance_result') and interview.performance_result 
                            else None),
            'decision': (interview.performance_result.decision 
                        if hasattr(interview, 'performance_result') and interview.performance_result 
                        else None),
            'notification_sent': interview.notification_sent,
            'email_sent': interview.email_sent,
            'reminder_sent': interview.reminder_sent,
        }