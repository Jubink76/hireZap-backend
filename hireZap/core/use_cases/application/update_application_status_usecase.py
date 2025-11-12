from core.interface.application_repository_port import ApplicationRepositoryPort

class UpdateApplicationStatusUsecase:
    def __init__(self,repository:ApplicationRepositoryPort):
        self.repository = repository
    
    def execute(self,application_id:int, status:str) -> dict:
        try:
            valid_status = ['applied', 'under_review',  'qualified','shortlisted', 'interview_scheduled', 
                            'interviewed', 'offered', 'rejected', 'withdrawn', 'hired']
            if status not in valid_status:
                return {
                    'success':False,
                    'error': "Invalid status"
                }
            application = self.repository.update_application_status(application_id,status)
            if not application:
                return {
                    'success':False,
                    'error':"update status failed"
                }
            return {
                'success': True,
                'data':application.to_dict()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }