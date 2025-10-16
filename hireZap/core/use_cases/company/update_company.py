from core.entities.company import Company
from core.interface.company_repository_port import CompanyRepositoryPort

class UpdateCompanyUseCase:
    def __init__(self,company_repository: CompanyRepositoryPort):
        self.company_repository =company_repository
    
    def execute(self, recruiter_id:int, company_data:dict) -> dict:
        company = self.company_repository.get_company_by_recruiter_id(recruiter_id)
        if not company:
            return {
                'success': False,
                'error': 'Company not found'
            }
        update_company = self.company_repository.update_company(
            company.id,
            company_data
        )
        return {
            'success': True,
            'company': update_company.to_dict()
        }