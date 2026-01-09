"""
core/use_cases/telephonic_round/get_interview_details_usecase.py
"""
from typing import Dict, Optional
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort


class GetInterviewDetailsUseCase:
    """
    Get complete interview details including transcription and analysis
    """
    
    def __init__(self, repository: TelephonicRoundRepositoryPort):
        self.repository = repository
    
    def execute(self, interview_id: int, user_id: int) -> Dict:
        """
        Get detailed interview information
        
        Args:
            interview_id: Interview ID
            user_id: Requesting user ID (for authorization)
        
        Returns:
            Complete interview details with transcription and analysis
        """
        
        # 1. Get interview with all related data
        interview = self.repository.get_interview_by_id(interview_id)
        
        if not interview:
            return {
                'success': False,
                'error': 'Interview not found'
            }
        
        # 2. Authorization check
        # User must be either the recruiter or the candidate
        is_recruiter = hasattr(interview.job, 'recruiter_id') and interview.job.recruiter_id == user_id
        is_candidate = interview.application.candidate_id == user_id
        is_conducted_by = interview.conducted_by_id == user_id
        
        if not (is_recruiter or is_candidate or is_conducted_by):
            return {
                'success': False,
                'error': 'Unauthorized access to interview details'
            }
        
        # 3. Build comprehensive response
        result = {
            'success': True,
            'interview': {
                'id': interview.id,
                'status': interview.status,
                
                # Candidate info
                'candidate': {
                    'id': interview.application.candidate_id,
                    'name': f"{interview.application.first_name} {interview.application.last_name}",
                    'email': interview.application.email,
                    'phone': interview.application.phone,
                },
                
                # Job info
                'job': {
                    'id': interview.job_id,
                    'title': interview.job.job_title,
                },
                
                # Schedule info
                'schedule': {
                    'scheduled_at': interview.scheduled_at.isoformat() if interview.scheduled_at else None,
                    'duration_minutes': interview.scheduled_duration_minutes,
                    'timezone': interview.timezone,
                    'notes': interview.scheduling_notes,
                },
                
                # Actual timing
                'actual': {
                    'started_at': interview.started_at.isoformat() if interview.started_at else None,
                    'ended_at': interview.ended_at.isoformat() if interview.ended_at else None,
                    'duration_seconds': interview.actual_duration_seconds,
                },
                
                # Notifications
                'notifications': {
                    'notification_sent': interview.notification_sent,
                    'email_sent': interview.email_sent,
                    'reminder_sent': interview.reminder_sent,
                },
            }
        }
        
        # 4. Add call session details if exists
        if hasattr(interview, 'call_session') and interview.call_session:
            result['interview']['call_session'] = {
                'session_id': interview.call_session.session_id,
                'connection_quality': interview.call_session.connection_quality,
                'recording_url': interview.call_session.recording_url,
                'recording_duration_seconds': interview.call_session.recording_duration_seconds,
            }
        
        # 5. Add transcription if exists (only for recruiters)
        if is_recruiter or is_conducted_by:
            if hasattr(interview, 'transcription') and interview.transcription:
                transcription = interview.transcription
                
                # Only include full transcription if completed
                if transcription.processing_status == 'completed':
                    result['interview']['transcription'] = {
                        'full_text': transcription.full_text,
                        'segments': transcription.segments,
                        'detected_language': transcription.detected_language,
                        'confidence': transcription.confidence,
                    }
                else:
                    result['interview']['transcription'] = {
                        'status': transcription.processing_status,
                        'error': transcription.error_message,
                    }
        
        # 6. Add performance results
        performance = self.repository.get_performance_result(interview_id)
        
        if performance:
            result['interview']['performance'] = {
                # Scores
                'scores': {
                    'overall': performance.overall_score,
                    'communication': performance.communication_score,
                    'technical_knowledge': performance.technical_knowledge_score,
                    'problem_solving': performance.problem_solving_score,
                    'enthusiasm': performance.enthusiasm_score,
                    'clarity': performance.clarity_score,
                    'professionalism': performance.professionalism_score,
                },
                
                # Decision
                'decision': performance.decision,
                
                # Analysis
                'analysis': {
                    'summary': performance.ai_summary,
                    'highlights': performance.key_highlights,
                    'improvements': performance.areas_for_improvement,
                    'technical_assessment': performance.technical_assessment,
                    'communication_assessment': performance.communication_assessment,
                    'topics_discussed': performance.key_topics_discussed,
                    'questions_asked': performance.questions_asked_count,
                },
                
                # Manual override (if exists)
                'manual_override': None,
            }
            
            # Add manual override details if exists
            if performance.manual_score_override is not None:
                result['interview']['performance']['manual_override'] = {
                    'score': performance.manual_score_override,
                    'decision': performance.manual_decision_override,
                    'reason': performance.override_reason,
                    'overridden_at': performance.overridden_at.isoformat() if performance.overridden_at else None,
                }
            
            # Add final values
            result['interview']['performance']['final_score'] = performance.final_score
            result['interview']['performance']['final_decision'] = performance.final_decision
        
        return result