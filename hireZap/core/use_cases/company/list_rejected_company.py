from core.interface.company_repository_port import CompanyRepositoryPort

class ListRejectedCompanyUsecase:
    def __init__(self,company_repo = CompanyRepositoryPort):
        self.company_repo = company_repo
    
    def execute(self):
        companies = self.company_repo.get_rejected_companies()
        if not companies:
            return {
                'success' : False,
                'error' : "No rejected companies found"
            }
        return {
            'success' : True,
            'companies' : [company.to_dict() for company in companies]
        }