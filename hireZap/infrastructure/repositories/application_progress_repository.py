from typing import Dict, List, Optional
from django.db.models import Q
from django.conf import settings
from core.interface.application_progress_repository_port import ApplicationProgressRepositoryPort
from core.entities.selection_stage import SelectionStage as SelectionStageEntity
from application.models import ApplicationModel, ApplicationStageHistory
from selection_process.models import SelectionProcessModel
from telephonic_round.models import TelephonicInterview, InterviewPerformanceResult,CallSession
from hr_round.models import HRInterview
import logging

logger = logging.getLogger(__name__)

class ApplicationProgressRepository(ApplicationProgressRepositoryPort):
    
    def get_application_by_id(self, application_id: int, candidate_id: int):
        """Get application by ID ensuring candidate ownership"""
        return ApplicationModel.objects.select_related(
            'job', 
            'job__company', 
            'candidate',
            'current_stage'
        ).get(
            id=application_id,
            candidate_id=candidate_id
        )
    
    def get_job_stages(self, job_id: int) -> List[SelectionStageEntity]:
        """Get job's selection process stages ordered by sequence"""
        try:
            processes = SelectionProcessModel.objects.filter(
                job_id=job_id,
                is_active=True
            ).select_related('stage').order_by('order')
            
            if not processes.exists():
                all_processes = SelectionProcessModel.objects.filter(job_id=job_id)
            stages = []
            for idx, process in enumerate(processes, 1):
                stage = process.stage
                
                # Create stage entity with order from process
                stage_entity = SelectionStageEntity(
                    id=stage.id,
                    slug=stage.slug,
                    name=stage.name,
                    description=stage.description,
                    icon=stage.icon,
                    duration=stage.duration,
                    requires_premium=stage.requires_premium,
                    tier=stage.tier,
                    is_default=stage.is_default,
                    order=process.order,
                    is_active=stage.is_active,
                    created_at=stage.created_at,
                    updated_at=stage.updated_at
                )
                stages.append(stage_entity)
            
            return stages
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error fetching job selection stages: {str(e)}")
            return []
    
    def get_resume_screening_progress(self, application_id: int) -> Optional[Dict]:
        """Get resume screening progress for application"""
        try:
            application = ApplicationModel.objects.get(id=application_id)
            
            # Check if screening is completed
            if application.screening_status != 'completed':
                return None
            
            return {
                'status': 'completed',
                'result': application.ats_decision,
                'score': application.ats_overall_score,
                'completed_at': application.updated_at if application.screening_status == 'completed' else None,
                'feedback': f"Skills: {application.ats_skills_score}, Experience: {application.ats_experience_score}, Education: {application.ats_education_score}" if application.ats_overall_score else None
            }
        except ApplicationModel.DoesNotExist:
            return None
    
    def get_telephonic_interview_progress(self, application_id: int) -> Optional[Dict]:
        """Get telephonic interview progress for application"""
        try:
            interview = TelephonicInterview.objects.select_related(
                'performance_result',
                'call_session'  
            ).get(
                application_id=application_id
            )
            
            # Get performance result if exists
            performance = None
            score = None
            result = None
            feedback = None
            
            try:
                performance = interview.performance_result
                score = performance.final_score
                result = 'passed' if performance.final_decision == 'qualified' else 'failed' if performance.final_decision == 'not_qualified' else None
                feedback = performance.ai_summary
            except InterviewPerformanceResult.DoesNotExist:
                pass
            
            # Calculate actual duration if interview completed
            actual_duration = None
            if interview.started_at and interview.ended_at:
                duration_seconds = (interview.ended_at - interview.started_at).total_seconds()
                actual_duration = int(duration_seconds / 60)  # Convert to minutes
            
            # GET SESSION_ID from active call session
            session_id = None
            try:
                # Direct access - OneToOne relationship
                call_session = interview.call_session
                if call_session:
                    session_id = call_session.session_id
            except CallSession.DoesNotExist:
                # No call session exists yet
                session_id = None
            except AttributeError:
                # call_session attribute doesn't exist
                session_id = None
            
            return {
                'interview_id': interview.id,
                'status': interview.status,
                'result': result,
                'score': score,
                'scheduled_at': interview.scheduled_at,
                'started_at': interview.started_at,
                'completed_at': interview.ended_at,
                'feedback': feedback,
                'actual_duration_minutes': actual_duration,
                'session_id': session_id  
            }
        except TelephonicInterview.DoesNotExist:
            return None
    
    def get_hr_interview_progress(self, application_id: int) -> Optional[Dict]:
        """Get HR interview progress for application"""
        try:
            interview = HRInterview.objects.select_related(
                'application',
                'notes',
                'result'
            ).get(application_id=application_id)
        
            session = None
            try:
                session = interview.meeting_session
            except Exception:
                session = None
            
            # Get notes/score if exists
            score = None
            result = None
            feedback = None
            
            try:
                if hasattr(interview, 'notes') and interview.notes:
                    score = interview.notes.calculated_score
                    result = 'passed' if score and score >= 70 else 'failed' if score else None
                    feedback = interview.notes.overall_impression
            except Exception:
                pass

            session_id = None
            zegocloud_config = None
            
            if session and not session.ended_at and interview.status in ['in_progress', 'candidate_joined']:
                session_id = session.session_id
                
                try:
                    from infrastructure.services.hr_round_service import MeetingService
                    
                    candidate_id = str(interview.application.candidate_id)
                    logger.info(f"Generating token for candidate_id={candidate_id}, room_id={session.room_id}")
                    candidate_token = MeetingService.generate_zegocloud_token(
                        user_id=candidate_id,
                        room_id=session.room_id
                    )
                    
                    zegocloud_config = {
                        'app_id': settings.ZEGOCLOUD_APP_ID,
                        'room_id': session.room_id,
                        'token': candidate_token,
                        'user_id': candidate_id,
                    }
                    
                    logger.info(f"ZegoCloud config generated for candidate {candidate_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate ZegoCloud config: {e}")
                    zegocloud_config = None
            
            # Calculate actual duration if completed
            actual_duration = None
            if session and session.started_at and session.ended_at:
                duration_seconds = (session.ended_at - session.started_at).total_seconds()
                actual_duration = int(duration_seconds / 60)
            
            return {
                'interview_id': interview.id,
                'status': interview.status,
                'result': result,
                'score': score,
                'scheduled_at': interview.scheduled_at,
                'started_at': interview.started_at,
                'completed_at': interview.ended_at,
                'feedback': feedback,
                'actual_duration_minutes': actual_duration,
                'session_id': session_id,
                'zegocloud_config': zegocloud_config,
                'session_started_at': session.started_at.isoformat() if session and session.started_at else None
                
            }
            
        except HRInterview.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting HR interview progress: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def get_stage_history(self, application_id: int, stage_id: int) -> Optional[Dict]:
        """Get stage history for application"""
        try:
            history = ApplicationStageHistory.objects.get(
                application_id=application_id,
                stage_id=stage_id
            )
            
            return {
                'status': history.status,
                'started_at': history.started_at,
                'completed_at': history.completed_at,
                'feedback': history.feedback
            }
        except ApplicationStageHistory.DoesNotExist:
            return None