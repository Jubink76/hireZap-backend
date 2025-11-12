from core.interface.application_repository_port import ApplicationRepositoryPort

class GetApplicationByIdUsecase:
    def __init__(self,repository:ApplicationRepositoryPort):
        self.repository = repository
    
    def execute(self,application_id:int) -> dict:
        try:
            application = self.repository.get_application_by_id(application_id)
            if not application:
                return {
                    'success':False,
                    'error' : "Failed to fetch application"
                }
            return {
                'success':True,
                'data':application.to_dict()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

        