from typing import Optional, List
from abc import ABC, abstractmethod
from core.entities.application import Application

class ApplicationRepositoryPort(ABC):

    @abstractmethod
    def create_application(self,application:Application) -> Optional[Application]:
        """ Create new application """
        return NotImplementedError
    
    @abstractmethod
    def get_application_by_id(self,appilcation_id:int) -> Optional[Application]:
        """ Get application by id """
        return NotImplementedError
    
    @abstractmethod
    def get_application_by_job_and_candidate(self, job_id: int, candidate_id: int) -> Optional[Application]:
        """Get application by job and candidate (for checking duplicates)""" 
        return NotImplementedError

    @abstractmethod
    def get_applications_by_candidate(self,candidate_id:int) -> List[Application]:
        """ Get all application by candidate """
        return NotImplementedError
    
    @abstractmethod
    def get_applications_by_job(self,job_id:int) -> List[Application]:
        """ Get all application in the job """
        return NotImplementedError
    
    @abstractmethod
    def get_applications_by_status(self,job_id:int, status:str) -> List[Application]:
        """ Get applications by status of perticular job """
        return NotImplementedError
    
    @abstractmethod
    def update_application(self, application_id: int, application_data: dict) -> Optional[Application]:
        """Update an application"""
        return NotImplementedError

    @abstractmethod
    def update_application_status(self, application_id: int, status: str) -> Optional[Application]:
        """Update application status"""
        return NotImplementedError

    @abstractmethod
    def delete_application(self, application_id: int) -> bool:
        """Delete an application (or mark as withdrawn)"""
        return NotImplementedError

    @abstractmethod
    def get_candidate_draft(self, candidate_id: int, job_id: int) -> Optional[Application]:
        """Get candidate's draft application for a specific job"""
        return NotImplementedError