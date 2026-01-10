from typing import Dict
from core.interface.application_progress_repository_port import ApplicationProgressRepositoryPort

class GetApplicationProgressUseCase:
    """Use case for getting application stage progress"""
    
    def __init__(self, repository: ApplicationProgressRepositoryPort):
        self.repository = repository
    
    def execute(self, application_id: int, candidate_id: int) -> Dict:
        """
        Execute the use case to get application progress
        
        Args:
            application_id: ID of the application
            candidate_id: ID of the candidate (to verify ownership)
            
        Returns:
            Dictionary containing application progress data
        """
        try:
            # Get application with related data
            application = self.repository.get_application_by_id(application_id, candidate_id)
            # Get job's configured stages
            job_stages = self.repository.get_job_stages(application.job_id)

            # If no stages configured, return basic application info
            if not job_stages:
                return {
                    'success': True, 
                    'application_id': application.id,
                    'job_id': application.job_id,
                    'job_title': application.job.job_title,
                    'company_name': application.job.company.company_name if application.job.company else None,
                    'company_logo': application.job.company.logo_url if application.job.company else None,
                    'current_stage': application.current_stage.slug if application.current_stage else None,
                    'current_stage_status': application.current_stage_status,
                    'applied_at': application.submitted_at or application.created_at,
                    'progress': {
                        'completed': 0,
                        'total': 0,
                        'percentage': 0
                    },
                    'stages': [],
                    'warning': 'No selection process configured for this job' 
                }
            
            # Build progress for each stage
            stage_progress = []
            
            for job_stage in job_stages:
                stage = job_stage
                progress_data = self._get_stage_progress(
                    stage=stage,
                    application=application,
                    application_id=application_id
                )
                stage_progress.append(progress_data)
            
            # Calculate overall progress
            completed_count = len([s for s in stage_progress if s['status'] == 'completed'])
            total_count = len(stage_progress)
            progress_percentage = round((completed_count / total_count) * 100) if total_count > 0 else 0
            
            # Build response
            return {
                'success': True,
                'application_id': application.id,
                'job_id': application.job_id,
                'job_title': application.job.job_title,
                'company_name': application.job.company.company_name if application.job.company else None,
                'company_logo': application.job.company.logo_url if application.job.company else None,
                'current_stage': application.current_stage.slug if application.current_stage else None,
                'current_stage_status': application.current_stage_status,
                'applied_at': application.submitted_at or application.created_at,
                'progress': {
                    'completed': completed_count,
                    'total': total_count,
                    'percentage': progress_percentage
                },
                'stages': stage_progress
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get application progress: {str(e)}'
            }
    
    def _get_stage_progress(self, stage, application, application_id: int) -> Dict:
        """
        Get progress data for a specific stage
        
        Args:
            stage: The SelectionStageModel object
            application: The ApplicationModel object
            application_id: ID of the application
            
        Returns:
            Dictionary containing stage progress data
        """
        # Base progress data
        progress_data = {
            'stage_id': stage.id,
            'stage_name': stage.name,
            'stage_slug': stage.slug,
            'stage_icon': stage.icon,
            'status': 'pending',
            'result': None,
            'score': None,
            'feedback': None,
            'started_at': None,
            'completed_at': None,
            'scheduled_at': None,
            'interview_id': None
        }
        
        # Check if this stage matches the current stage
        is_current_stage = (
            application.current_stage and 
            application.current_stage.id == stage.id
        )
        
        # Check stage history first
        history = self.repository.get_stage_history(application_id, stage.id)
        if history:
            if history['status'] == 'qualified':
                progress_data['status'] = 'completed'
                progress_data['result'] = 'passed'
            elif history['status'] == 'rejected':
                progress_data['status'] = 'completed'
                progress_data['result'] = 'failed'
            elif history['status'] == 'started':
                progress_data['status'] = 'in_progress'
            
            progress_data['started_at'] = history['started_at']
            progress_data['completed_at'] = history['completed_at']
            progress_data['feedback'] = history['feedback']
        
        # Check Resume Screening
        if stage.slug == 'resume-screening':
            screening_data = self.repository.get_resume_screening_progress(application_id)
            if screening_data:
                progress_data.update(screening_data)
                # Override result based on ats_decision
                if application.ats_decision == 'qualified':
                    progress_data['result'] = 'passed'
                elif application.ats_decision == 'rejected':
                    progress_data['result'] = 'failed'
            elif is_current_stage:
                if application.screening_status == 'processing':
                    progress_data['status'] = 'in_progress'
                elif application.screening_status == 'pending':
                    progress_data['status'] = 'pending'
        
        # Check Telephonic Round
        elif stage.slug == 'telephonic-round':
            telephonic_data = self.repository.get_telephonic_interview_progress(application_id)
            if telephonic_data:
                progress_data.update(telephonic_data)
            elif is_current_stage:
                progress_data['status'] = 'in_progress'
        
        # For other stages, check if current and set status accordingly
        elif is_current_stage:
            if application.current_stage_status == 'qualified':
                progress_data['status'] = 'completed'
                progress_data['result'] = 'passed'
            elif application.current_stage_status == 'rejected':
                progress_data['status'] = 'completed'
                progress_data['result'] = 'failed'
            elif application.current_stage_status == 'started':
                progress_data['status'] = 'in_progress'
            else:
                progress_data['status'] = 'pending'
        
        return progress_data