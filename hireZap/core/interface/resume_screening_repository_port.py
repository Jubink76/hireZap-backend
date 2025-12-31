from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class ResumeScreeningRepositoryPort(ABC):
    @abstractmethod
    def get_application_by_id(self,application_id:int):
        """Get application with related data"""
        raise NotImplementedError
    
    @abstractmethod
    def update_screening_status(self,application_id:int, status:str):
        """Update application screening status"""
        raise NotImplementedError
    
    @abstractmethod
    def save_screening_results(self,application_id:int, results:Dict) -> bool:
        """Save complete screening result"""
        raise NotImplementedError
    
    @abstractmethod
    def update_job_progress(self,job_id:int):
        """Updat job screening progress count"""
        raise NotImplementedError
    
    @abstractmethod
    def get_pending_applications_by_job(self,job_id:int):
        """Get all pending application for a job"""
        raise NotImplementedError
    
    @abstractmethod
    def mark_screening_as_failed(self, application_id:int, error:str, retry_count:int):
        """Mark application screening as failed"""
        raise NotImplementedError
    
    @abstractmethod
    def update_job_screening_status(self,job_id:int, status:str, **kwargs):
        """Update job screening status"""
        raise NotImplementedError
    
    @abstractmethod
    def check_all_screening_complete(self, job_id:int) -> bool:
        """Check if all screening completed"""
        raise NotImplementedError
    
    @abstractmethod
    def get_screening_results(self,job_id:int, filters:Optional[Dict] = None) -> List[Dict]:
        """Get screening results of a job with filters"""
        raise NotImplementedError
    
    @abstractmethod
    def move_to_next_stage(self,application_id:int , feedback:str=None) -> Dict:
        """Move application to next stage"""
        raise NotImplementedError
    
    @abstractmethod
    def get_job_by_id(self,job_id:int):
        """Get job by id"""
        raise NotImplementedError
    
