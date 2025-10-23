from typing import Optional, List
from decimal import Decimal 
from companies.models import Company as CompanyModel
from core.entities.company import Company
from core.interface.company_repository_port import CompanyRepositoryPort

class CompanyRepository(CompanyRepositoryPort):
    """ Django implementation of company repository"""

    def _model_to_entity(self,company_model:CompanyModel) -> Company:
        return Company(
            id=company_model.id,
            recruiter_id=company_model.recruiter_id,
            company_name=company_model.company_name,
            logo_url=company_model.logo_url,
            business_certificate=company_model.business_certificate,
            business_email=company_model.business_email,
            phone_number=company_model.phone_number,
            industry=company_model.industry,
            company_size=company_model.company_size,
            website=company_model.website,
            linkedin_url=company_model.linkedin_url,
            address=company_model.address,
            latitude=company_model.latitude,
            longitude=company_model.longitude,
            verification_status=company_model.verification_status,
            founded_year=company_model.founded_year,
            description=company_model.description,
            created_at=company_model.created_at,
            updated_at=company_model.updated_at
        )
    
    def create_company(self,company:Company) -> Company:
        """ Create new company """
        company_model = CompanyModel.objects.create(
            recruiter_id=company.recruiter_id,
            company_name=company.company_name,
            logo_url=company.logo_url,
            business_certificate=company.business_certificate,
            business_email=company.business_email,
            phone_number=company.phone_number,
            industry=company.industry,
            company_size=company.company_size,
            website=company.website,
            linkedin_url=company.linkedin_url,
            address=company.address,
            latitude=company.latitude,
            longitude=company.longitude,
            verification_status=company.verification_status,
            founded_year=company.founded_year,
            description=company.description
        )
        return self._model_to_entity(company_model)
    
    def get_company_by_id(self, company_id:int) -> Optional[Company]:
        try:
            company_model = CompanyModel.objects.get(id=company_id)
            return self._model_to_entity(company_model)
        except CompanyModel.DoesNotExist:
            return None
    
    def get_company_by_recruiter_id(self,recruiter_id:int) -> Optional[Company]:
        try:
            company_model = CompanyModel.objects.get(recruiter_id=recruiter_id)
            return self._model_to_entity(company_model)
        except CompanyModel.DoesNotExist:
            return None
    
    def update_company(self,company_id:int, company_data:dict) -> Optional[Company]:
        try:
            company_model = CompanyModel.objects.get(id=company_id)
            for key, value in company_data.items():
                if hasattr(company_model, key):
                    setattr(company_model, key,value)
            company_model.save()
            return self._model_to_entity(company_model)
        except CompanyModel.DoesNotExist:
            return None
  
    def approve_company(self, company_id:int) -> Optional[Company]:
        try:
            company_model = CompanyModel.objects.get(id=company_id)
            company_model.verification_status = 'verified'
            company_model.save(update_fields = ['verification_status', 'updated_at'])
            return self._model_to_entity(company_model)
        except CompanyModel.DoesNotExist:
            return None
    
    def reject_company(self, company_id:int, reason:str) -> Optional[Company]:
        try:
            company_model = CompanyModel.objects.get(id=company_id)
            company_model.verification_status = 'rejected'
            company_model.rejection_reason = reason
            company_model.save(update_fields=['verification_status','updated_at','rejection_reason'])
            return self._model_to_entity(company_model)
        except CompanyModel.DoesNotExist:
            return None
    
    def get_pending_companies(self) -> List[Company]:
        companies = CompanyModel.objects.filter(verification_status = 'pending')
        return [self._model_to_entity(c) for c in companies]
    
    def get_verified_companies(self) -> List[Company]:
        companies = CompanyModel.objects.filter(verification_status = 'verified')
        return [self._model_to_entity(c) for c in companies]
    
    def get_rejected_companies(self) -> List[Company]:
        companies = CompanyModel.objects.filter(verification_status = 'rejected')
        return [self._model_to_entity(c) for c in companies]
    
    def delete_company(self, company_id: int) -> bool:
        try:
            company_model = CompanyModel.objects.get(id=company_id)
            company_model.delete()
            return True
        except CompanyModel.DoesNotExist:
            return False
        
    def company_exists_for_recruiter(self, recruiter_id:int) -> bool:
        return CompanyModel.objects.filter(recruiter_id= recruiter_id).exists()