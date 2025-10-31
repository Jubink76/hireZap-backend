from core.interface.job_repository_port import JobRepositoryPort
from typing import Dict, Any

class FetchActiveJobsUsecase:
    def __init__(self,job_repository:JobRepositoryPort):
        self.job_repo = job_repository
    
    def execute(self):
        jobs = self.job_repo.get_all_active_jobs()
        if not jobs:
            return {
                'success' : False,
                'error' : "Failed to get jobs "
            }
        return {
            'success': True,
            'jobs' : [job.to_dict() for job in jobs]
        }
