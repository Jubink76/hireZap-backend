"""
core/use_cases/telephonic_round/get_telephonic_candidates_usecase.py
CORRECTED: Fetches candidates in telephonic stage + their interview status
"""
from typing import Dict, Optional
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort


class GetTelephonicRoundCandidates:
    """
    Get candidates in telephonic round stage
    Shows both:
    1. Candidates who just moved here (no interview scheduled yet)
    2. Candidates with scheduled/completed interviews
    """
    
    def __init__(self, repository: TelephonicRoundRepositoryPort):
        self.repository = repository
    
    def execute(self, job_id: int, status_filter: Optional[str] = None):
        try:
            # 1. Get all candidates who are in telephonic-round stage
            # These are candidates who qualified from resume screening
            stage_candidates = self.repository.get_candidates_for_telephonic_round(job_id)
            
            # 2. Get all existing interviews for this job
            all_interviews = self.repository.get_interviews_by_job(job_id, status=None)
            
            # 3. Create a map of application_id -> interview
            interview_map = {
                interview.application_id: interview 
                for interview in all_interviews
            }
            
            # 4. Build candidate list with interview status
            candidates = []
            for application in stage_candidates:
                # Check if this candidate has an interview
                interview = interview_map.get(application.id)
                
                if interview:
                    # Has interview - serialize interview data
                    candidate_data = self._serialize_interview(interview)
                else:
                    # No interview yet - create placeholder
                    candidate_data = self._serialize_candidate_without_interview(application)
                
                candidates.append(candidate_data)
            
            # 5. Apply status filter if provided
            if status_filter:
                candidates = [c for c in candidates if c['status'] == status_filter]
            
            # 6. Get statistics
            stats = self.repository.get_job_interview_stats(job_id)
            
            # 7. Calculate not_scheduled count
            not_scheduled_count = len([c for c in candidates if c['status'] == 'not_scheduled'])
            stats['not_scheduled'] = not_scheduled_count
            stats['total_candidates'] = len(candidates)
            
            return {
                'success': True,
                'candidates': candidates,
                'total': len(candidates),
                'stats': stats
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Failed to fetch candidates: {str(e)}'
            }
    
    def _serialize_interview(self, interview) -> Dict:
        """Convert interview model to dictionary"""
        actual_duration_seconds = None
        if interview.actual_duration_minutes:
            actual_duration_seconds = interview.actual_duration_minutes * 60
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
            'actual_duration_minutes': interview.actual_duration_minutes,
            'actual_duration_seconds': actual_duration_seconds,
            'has_recording': bool(
                hasattr(interview, 'call_session') and 
                interview.call_session and 
                interview.call_session.recording_url
            ),
            'has_transcription': bool(
                hasattr(interview, 'transcription') and 
                interview.transcription
            ),
            'has_results': bool(
                hasattr(interview, 'performance_result') and 
                interview.performance_result
            ),
            'overall_score': (
                interview.performance_result.overall_score 
                if hasattr(interview, 'performance_result') and interview.performance_result 
                else None
            ),
            'decision': (
                interview.performance_result.decision 
                if hasattr(interview, 'performance_result') and interview.performance_result 
                else None
            ),
            'notification_sent': interview.notification_sent,
            'email_sent': interview.email_sent,
            'reminder_sent': interview.reminder_sent,
            # Include current stage info
            'current_stage': {
                'id': interview.application.current_stage.id if interview.application.current_stage else None,
                'name': interview.application.current_stage.name if interview.application.current_stage else None,
                'slug': interview.application.current_stage.slug if interview.application.current_stage else None,
            } if hasattr(interview.application, 'current_stage') else None,
        }
    
    def _serialize_candidate_without_interview(self, application) -> Dict:
        """
        Serialize candidate who doesn't have an interview yet
        Status: 'not_scheduled'
        """
        return {
            'interview_id': None,  # No interview created yet
            'application_id': application.id,
            'candidate': {
                'id': application.candidate_id,
                'name': f"{application.first_name} {application.last_name}",
                'email': application.email,
                'phone': getattr(application, 'phone', None),
            },
            'status': 'not_scheduled',  # Not scheduled yet
            'scheduled_at': None,
            'duration': None,
            'timezone': None,
            'started_at': None,
            'ended_at': None,
            'actual_duration_seconds': None,
            'has_recording': False,
            'has_transcription': False,
            'has_results': False,
            'overall_score': None,
            'decision': None,
            'notification_sent': False,
            'email_sent': False,
            'reminder_sent': False,
            # Include current stage info
            'current_stage': {
                'id': application.current_stage.id if application.current_stage else None,
                'name': application.current_stage.name if application.current_stage else None,
                'slug': application.current_stage.slug if application.current_stage else None,
            } if hasattr(application, 'current_stage') else None,
        }