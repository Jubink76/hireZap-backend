from core.interface.application_repository_port import ApplicationRepositoryPort

class GetApplicationByJobUsecase:
    def __init__(self,repository:ApplicationRepositoryPort):
        self.repository=repository
    
    def execute(self,job_id:int, status:str = None) -> dict:
        """Get all applications for a job, optionally filtered by status"""
        try:
            if status:
                applications = self.repository.get_applications_by_status(job_id,status)
            else:
                applications = self.repository.get_applications_by_job(job_id)
            
            if not applications:
                return {
                    'success':False,
                    'error':"Failed to fetch applications"
                }
            return {
                'success':True,
                'data':[app.to_dict() for app in applications],
                'count':len(applications)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }