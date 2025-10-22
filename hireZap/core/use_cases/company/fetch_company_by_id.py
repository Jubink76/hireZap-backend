from core.interface.company_repository_port import CompanyRepositoryPort
class FetchCompanyByIdUsecase:
    def __init__(self,company_repository:CompanyRepositoryPort):
        self.company_repository = company_repository

    def execute(self,company_id: int) -> dict:
        company = self.company_repository.get_company_by_id(company_id)
        if not company:
            return {
                'success': False,
                'error' : "Company not found"
            }
        return {
            'success' : True,
            'company' : company.to_dict()
        }