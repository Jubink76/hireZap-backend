from core.interface.application_repository_port import ApplicationRepositoryPort

class CheckApplicationExistsUseCase:
    def __init__(self, repository: ApplicationRepositoryPort):
        self.repository = repository

    def execute(self, job_id: int, candidate_id: int) -> dict:
        """Check if candidate has already applied or has a draft"""
        try:
            # Check for submitted application
            submitted = self.repository.get_application_by_job_and_candidate(job_id, candidate_id)
            
            # Check for draft
            draft = self.repository.get_candidate_draft(candidate_id, job_id)
            
            return {
                'success': True,
                'data': {
                    'has_applied': submitted is not None,
                    'has_draft': draft is not None,
                    'application': submitted.to_dict() if submitted else None,
                    'draft': draft.to_dict() if draft else None
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }