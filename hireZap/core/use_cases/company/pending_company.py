from core.entities.company import Company
from core.interface.company_repository_port import CompanyRepositoryPort

class GetPendingCompanyUseCase:
    def __init__(self,company_repository:CompanyRepositoryPort):
        self.company_repository = company_repository
    
    def execute(self) -> dict:
        companies = self.company_repository.get_pending_companies()
        if not companies:
            return {
                'success': False,
                'error': "No pending companies found"
            }
        return {
            'success': True,
            'companies': [company.to_dict() for company in companies]
        }