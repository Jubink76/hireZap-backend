from core.interface.company_repository_port import CompanyRepositoryPort
class ApproveCompanyUsecase:
    def __init__(self,comapny_repo:CompanyRepositoryPort):
        self.company_repo = comapny_repo

    def execute(self,company_id: int):
        company = self.company_repo.approve_company(company_id)
        if not company:
            return {
                'success': False,
                'error' : "Company not found"
            }
        return {
            'success' : True,
            'company' : company.to_dict()
        }