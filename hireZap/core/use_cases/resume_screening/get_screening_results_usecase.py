from typing import Dict, List, Optional
from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort

class GetScreeningResultsUseCase:
    
    def __init__(self, screening_repo: ResumeScreeningRepositoryPort):
        self.screening_repo = screening_repo
    
    def execute(self, job_id: int, filters: Optional[Dict] = None) -> Dict:
        
        # This will be implemented in repository
        results = self.screening_repo.get_screening_results(job_id, filters)
        
        return {
            'success': True,
            'results': results,
            'total': len(results)
        }