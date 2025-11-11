from core.interface.job_repository_port import JobRepositoryPort
class GetJobBYIdUsecase:
    def __init__(self,job_repo:JobRepositoryPort):
        self.job_repository = job_repo
    
    def execute(self,job_id:int):
        current_job = self.job_repository.get_job_by_id(job_id)
        if not current_job:
            return {
                'success': False,
                'error' : "Faild to fetch job data"
            }

        return {
            'success':True,
            'job' : current_job.to_dict()
        }