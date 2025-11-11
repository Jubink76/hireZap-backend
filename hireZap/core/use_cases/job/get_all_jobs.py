from core.interface.job_repository_port import JobRepositoryPort

class GetAllJobsUsecase:
    def __init__(self,job_repository:JobRepositoryPort):
        self.job_repo = job_repository
    
    def excecute(self):
        jobs = self.job_repo.get_all_jobs()
        if not jobs:
            return {
                'success': False,
                'error' : "Failed to fetch all jobs"
            }
        return {
            'success': True,
            'jobs' : [job.to_dict() for job in jobs]
        }
