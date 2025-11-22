from abc import abstractmethod, ABC
from typing import Optional, List, Dict, Any
from core.entities.admin_entity import (
    CandidateInfo,
    RecruiterInfo,
    JobInfo,
    ApplicationInfo,
    AdminDashboardStats
)

class AdminRepositoryPort(ABC):

    #dashboard
    @abstractmethod
    def get_dashboard_stats(self) -> AdminDashboardStats:
        """ Get admin dashboard Stats """
        raise NotImplementedError
    
    # candidate
    @abstractmethod
    def get_all_candidate(self, page: int=1,
                        page_size: int= 10,
                        filters: Optional[Dict[str, Any]] = None
                        ) -> tuple[List[CandidateInfo], int]:
        """ Get all candidates with pagination and filters """
        raise NotImplementedError
    
    @abstractmethod
    def candidate_by_id(self, user_id: int) -> Optional[CandidateInfo]:
        """ Get complete candidate details """
        raise NotImplementedError
    
    @abstractmethod
    def search_candidate(self, query:str) -> List[CandidateInfo]:
        """ Search Candidates """
        raise NotImplementedError
    
    # recruiters 
    @abstractmethod
    def get_all_recruiters(self, page:int = 1,
                           page_size: int = 10,
                           ) -> tuple[List[RecruiterInfo], int]:
        """ Get all recruiter with paginationn """
        raise NotImplementedError
    
    @abstractmethod
    def get_recruiter_by_id(self,user_id:int) -> Optional[RecruiterInfo]:
        """ Get complete recruiter Details """
        raise NotImplementedError
    
    # job
    @abstractmethod
    def get_all_jobs_with_detail(self,page:int=1,
                                 page_size:int = 10,
                                 ) -> tuple[List[JobInfo], int]:
        """ Get all jobs with details """
        raise NotImplementedError
    
    @abstractmethod
    def get_job_details(self, job_id:int) -> Optional[JobInfo]:
        """ Get job details of a perticular job"""
        raise NotImplementedError
    
    # applications 
    @abstractmethod
    def get_all_application_with_detail(self, page:int=1,
                                        page_size:int=10,
                                        ) -> tuple[List[ApplicationInfo],int]:
        """ Get all Application with detail """
        raise NotImplementedError
    
    @abstractmethod
    def get_application_details(self,application_id:int) -> Optional[ApplicationInfo]:
        """ Get complete application detail """
        raise NotImplementedError
    
    