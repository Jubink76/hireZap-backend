from typing import Dict, List, Optional
from django.db.models import Q
from core.interface.application_progress_repository_port import ApplicationProgressRepositoryPort
from core.entities.selection_stage import SelectionStage as SelectionStageEntity
from application.models import ApplicationModel, ApplicationStageHistory
from selection_process.models import SelectionProcessModel
from telephonic_round.models import TelephonicInterview, InterviewPerformanceResult

import logging

logger = logging.getLogger(__name__)

class ApplicationProgressRepository(ApplicationProgressRepositoryPort):
    """Repository for handling application progress data"""
    
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
                'performance_result'
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
            
            return {
                'interview_id': interview.id,
                'status': interview.status,
                'result': result,
                'score': score,
                'scheduled_at': interview.scheduled_at,
                'started_at': interview.started_at,
                'completed_at': interview.ended_at,
                'feedback': feedback,
                'actual_duration_minutes': actual_duration
            }
        except TelephonicInterview.DoesNotExist:
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