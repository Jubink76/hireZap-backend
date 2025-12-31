from typing import Dict
from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort

class GetScreeningProgressUseCase:
    """Get screening progress for a job"""
    
    def __init__(self, screening_repo: ResumeScreeningRepositoryPort):
        self.screening_repo = screening_repo
    
    def execute(self, job_id: int) -> Dict:
        """Get screening progress"""
        
        job = self.screening_repo.get_job_by_id(job_id)
        if not job:
            return {
                'success': False,
                'error': 'Job not found'
            }
        
        total = job.total_applications_count or 0
        screened = job.screened_applications_count or 0
        percentage = (screened / total * 100) if total > 0 else 0
        
        return {
            'success': True,
            'progress': {
                'status': job.screening_status,
                'total_applications': total,
                'screened_applications': screened,
                'pending_applications': total - screened,
                'percentage': percentage,
                'started_at': job.screening_started_at.isoformat() if job.screening_started_at else None,
                'completed_at': job.screening_completed_at.isoformat() if job.screening_completed_at else None,
            }
        }