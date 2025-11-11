from core.interface.job_repository_port import JobRepositoryPort

class GetInactiveJobsUsecase:
    def __init__(self,repository_port: JobRepositoryPort):
        self.repository_port = repository_port
    
    def execute(self):
        jobs = self.repository_port.get_all_inactive_jobs()
        if not jobs:
            return {
                'success': False,
                'error' : "Failed to fetch all jobs"
            }
        return {
            'success': True,
            'jobs' : [job.to_dict() for job in jobs]
        }