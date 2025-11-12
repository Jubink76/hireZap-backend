from core.interface.application_repository_port import ApplicationRepositoryPort

class GetApplicationByCandidateUsecase:
    def __init__(self, repository: ApplicationRepositoryPort):
        self.repository = repository
    
    def execute(self, candidate_id: int, include_drafts: bool = False) -> dict:
        try:
            applications = self.repository.get_applications_by_candidate(
                candidate_id, 
                include_drafts
            )
            if applications is None:  # Changed from 'not applications' to handle empty list
                return {
                    'success': False,
                    'error': "Failed to fetch applications"
                }
            
            return {
                'success': True,
                'data': [app.to_dict() for app in applications],
                'count': len(applications)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }