from abc import ABC, abstractmethod
from typing import Optional, List
from core.entities.company import Company

class CompanyRepositoryPort(ABC):
    """ Interface for company repository operations """

    @abstractmethod
    def create_company(self, company:Company) -> Company:
        """ Create new company """
        raise NotImplementedError
    
    @abstractmethod
    def get_company_by_id(self,company_id:int) -> Optional[Company]:
        """ get company by id """
        raise NotImplementedError
    
    @abstractmethod
    def get_company_by_recruiter_id(self,recruiter_id:int) -> Optional[Company]:
        """ Get company by recruiter Id """
        raise NotImplementedError  
    
    @abstractmethod
    def update_company(self,company_id:int, company_data:dict) -> Optional[Company]:
        """ Update company information """
        raise NotImplementedError
    
    @abstractmethod
    def update_verification_status(self, company_id:int, status:str, reason:str = None) -> Optional[Company]:
        """ update verification status """
        raise NotImplementedError
    
    @abstractmethod
    def get_pending_companies(self) -> List[Company]:
        """ list all the pending companies """
        raise NotImplementedError
    
    @abstractmethod
    def get_verified_companies(self) -> List[Company]:
        """ list all the verified companies """
        raise NotImplementedError
    
    @abstractmethod
    def delete_company(self, company_id:int) -> bool:
        """ Delete company """
        raise NotImplementedError
    
    @abstractmethod
    def company_exists_for_recruiter(self, recruiter_id:int) -> bool:
        """ Check if company exists for recruiter """
        raise NotImplementedError