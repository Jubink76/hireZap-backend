from core.interface.job_repository_port import JobRepositoryPort

class GetPausedJobsUsecase:
    def __init__(self,repository_port:JobRepositoryPort):
        self.repository_port = repository_port

    def execute(self):
        jobs = self.repository_port.get_all_paused_jobs()
        if not jobs:
            return {
                'success': False,
                'error' : "Failed to fetch all paused jobs"
            }
        return {
            'success': True,
            'jobs' : [job.to_dict() for job in jobs]
        }