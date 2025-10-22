from core.interface.company_repository_port import CompanyRepositoryPort
class RejectCompanyUsecase:
    def __init__(self,company_repo: CompanyRepositoryPort):
        self.company_repo  = company_repo
    
    def execute(self,company_id: int, reason:str):
        if not reason:
            return {
                'success': False,
                'error' : "Rejection reason is required"
            }
        company = self.company_repo.reject_company(company_id, reason)
        if not company:
            return {
                'success': False,
                'error' : "Company not found"
            }
        return {
            'success' : True,
            'company' : company.to_dict()
        }