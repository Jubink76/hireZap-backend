from core.entities.company import Company
from core.interface.company_repository_port import CompanyRepositoryPort

class UpdateCompanyUseCase:
    def __init__(self,company_repository: CompanyRepositoryPort):
        self.company_repository =company_repository
    
    def execute(self,company_id:int, recruiter_id:int, company_data:dict) -> dict:
        existing_company = self.company_repository.get_company_by_recruiter_id(recruiter_id)
        if not existing_company:
            return {
                'success': False,
                'error': 'Company not found'
            }
        update_data = {
            **company_data,
            'verification_status':'pending',
            'rejection_reason' : None
        }

        updated_company = self.company_repository.update_company(company_id,update_data)
        if not updated_company:
            return {
                'success' : False,
                'error' : 'Company updation failed'
            }
        return {
            'success' : True,
            'message': 'Company updated successfully. Pending verification.',
            'company' : updated_company.to_dict()
        }