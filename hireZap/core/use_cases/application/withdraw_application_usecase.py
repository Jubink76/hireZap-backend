from core.interface.application_repository_port import ApplicationRepositoryPort

class WithdrawApplicationUsecase:
    def __init__(self,repository:ApplicationRepositoryPort):
        self.repository = repository
    
    def execute(self,candidate_id:int, application_id:int) -> dict:
        """ Withdraw the application"""
        try:
            application = self.repository.get_application_by_id(application_id)
            if not application:
                return {
                    'success':False,
                    'error':'Application not found'
                }
            if application.candidate_id != candidate_id:
                return {
                    'success':False,
                    'error':"Unauthorized"
                }
            if not application.can_be_withdrawn():
                return {
                    'success':False,
                    'error':"Cannot withdraw application"
                }
            #update status to withdrawn
            updated_app = self.repository.update_application_status(application_id,'withdrawn')
            if not updated_app:
                return {
                    'success': False,
                    'error' : "Failed to withdraw application"
                }
            return{
                'success':True,
                'data':updated_app.to_dict(),
                'message': 'Application withdrawn successfully'
            }   
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            