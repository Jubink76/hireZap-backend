from core.entities.company import Company
from core.interface.company_repository_port import CompanyRepositoryPort

class CreateCompanyUseCase:
    def __init__(self,company_repository:CompanyRepositoryPort):
        self.company_repository = company_repository

    def execute(self, recruiter_id: int, company_data: dict) -> dict:
        #checking company already exist
        if self.company_repository.company_exists_for_recruiter(recruiter_id):
            return {
                'success': False,
                'error' : 'Company already exists for this recruiter'
            }
        company = Company(
            recruiter_id=recruiter_id,
            company_name=company_data.get('company_name'),
            logo_url=company_data.get('logo_url'),
            business_certificate=company_data.get('business_certificate'),
            business_email=company_data.get('business_email'),
            phone_number=company_data.get('phone_number'),
            industry=company_data.get('industry'),
            company_size=company_data.get('company_size'),
            website=company_data.get('website'),
            linkedin_url=company_data.get('linkedin_url'),
            address=company_data.get('address'),
            latitude=company_data.get('latitude'),
            longitude=company_data.get('longitude'),
            founded_year=company_data.get('founded_year'),
            description=company_data.get('description'),
            verification_status='pending'
        )
        
        created_company = self.company_repository.create_company(company)
        
        return {
            'success': True,
            'company': created_company.to_dict()
        }