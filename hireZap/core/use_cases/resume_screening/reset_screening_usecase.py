from typing import Dict
from django.db import transaction

from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort

class ResetScreeningUseCase:
    def __init__(self, screening_repo: ResumeScreeningRepositoryPort):
        self.screening_repo = screening_repo

    def execute(self, job_id: int) -> Dict:
        job = self.screening_repo.get_job_by_id(job_id)
        if not job:
            return {
                'success': False,
                'error': 'Job not found'
            }

        with transaction.atomic():
            # Reset job-level screening data
            self.screening_repo.reset_job_screening(job_id)

            # Reset all applications
            self.screening_repo.reset_applications_for_job(job_id)

            # Delete screening results
            self.screening_repo.delete_screening_results(job_id)

        return {
            'success': True,
            'message': 'Screening reset successfully'
        }