from core.entities.company import Company
from core.interface.company_repository_port import CompanyRepositoryPort

class VerifyCompanyUseCase:
    def __init__(self, company_repository: CompanyRepositoryPort):
        self.company_repository = company_repository
    def execute(self,company_id:int, status: str, reason: str= None) -> dict:
        if status not in ['verified','rejected']:
            return {
                'success' : False,
                'error' : "Invalid status, Must be verified or rejected"
            }
        updated_company = self.company_repository.update_verification_status(
            company_id,
            status,
            reason
        )
        if not updated_company:
            return {
                'success': False,
                'error' : 'Company not found'
            }
        return {
            'success':True,
            'company': updated_company.to_dict()
        }