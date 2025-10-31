from core.interface.job_repository_port import JobRepositoryPort

class GetJobsByRecruiterUsecase:
    def __init__(self,job_repository: JobRepositoryPort):
        self.job_repo = job_repository

    def execute(self,recruiter_id:int):
        jobs = self.job_repo.get_jobs_by_recruiter(recruiter_id)
        if not jobs:
            return {
                'success': False,
                'error' : "Failed to fetch created jobs"
            }
        return {
            'success': True,
            'jobs' : [job.to_dict() for job in jobs]
        }