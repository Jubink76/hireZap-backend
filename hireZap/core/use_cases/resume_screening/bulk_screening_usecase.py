from typing import Dict
from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort
from core.interface.ats_configuration_repository_port import ATSConfigurationRepositoryPort

class StartBulkScreeningUseCase:
    """Use case to start bulk screening for a job"""
    
    def __init__(
        self,
        screening_repo: ResumeScreeningRepositoryPort,
        ats_repo: ATSConfigurationRepositoryPort
    ):
        self.screening_repo = screening_repo
        self.ats_repo = ats_repo
    
    def execute(self, job_id: int) -> Dict:
        """Start bulk screening"""
        
        # 1. Verify job exists
        job = self.screening_repo.get_job_by_id(job_id)
        if not job:
            return {
                'success': False,
                'error': 'Job not found'
            }
        
        # 2. Check if screening already in progress
        if job.screening_status == 'in_progress':
            return {
                'success': False,
                'error': 'Screening already in progress'
            }
        
        # 3. Check if ATS is configured
        ats_config = self.ats_repo.get_by_job_id(job_id)
        if not ats_config:
            return {
                'success': False,
                'error': 'Please configure ATS settings first'
            }
        
        # 4. Check if there are pending applications
        pending_count = self.screening_repo.get_pending_applications_count(job_id)
        if pending_count == 0:
            return {
                'success': False,
                'error': 'No pending applications to screen'
            }
        
        # 5. Dispatch Celery task
        from resume_screening.tasks import start_bulk_screening
        task = start_bulk_screening.delay(job_id)
        
        return {
            'success': True,
            'message': 'Bulk screening started',
            'task_id': task.id,
            'job_id': job_id,
            'total_applications': pending_count
        }