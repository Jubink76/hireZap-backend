from abc import ABC, abstractmethod
from typing import List, Optional
from core.entities.job import Job

class JobRepositoryPort(ABC):

    @abstractmethod
    def create_job(self, job: Job) -> Optional[Job]:
        """ create a new job posting """
        raise NotImplementedError
    
    @abstractmethod
    def get_job_by_id(self, job_id:int) -> Optional[Job]:
        """ Get job by id """
        raise NotImplementedError
    
    @abstractmethod
    def get_jobs_by_recruiter(self,recruiter_id:int) -> List[Job]:
        """ Get all job by created recruiter id """
        raise NotImplementedError
    
    @abstractmethod
    def get_jobs_by_company(self,company_id:int) -> List[Job]:
        """ Get all job by company """
        raise NotImplementedError
    
    @abstractmethod 
    def update_job(self,job_id:int, job_data:dict) -> Optional[Job]:
        """ Update job infromation"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_job(self,job_id:int) -> bool:
        """ Delete a job """
        raise NotImplementedError
    
    @abstractmethod
    def get_all_jobs(self) -> List[Job]:
        """ Get all jobs"""
        raise NotImplementedError
    
    @abstractmethod
    def get_all_active_jobs(self) -> List[Job]:
        """ Get all active jobs """
        raise NotImplementedError
    
    @abstractmethod
    def get_all_inactive_jobs(self) -> List[Job]:
        """ Get all inactive jobs """
        raise NotImplementedError
    
    @abstractmethod
    def get_all_paused_jobs(self) -> List[Job]:
        """ Get all paused jobs """
        raise NotImplementedError
    
    @abstractmethod
    def get_paused_job_recruiter(self,recruiter_id:int) -> List[Job]:
        """ Get all paused Job by recruiter """
        raise NotImplementedError
    
    @abstractmethod
    def update_job_status(self, job_id:int, status: str) -> Optional[Job]:
        """ Update job status (active , paused , closed )"""
        raise NotImplementedError
    
    

