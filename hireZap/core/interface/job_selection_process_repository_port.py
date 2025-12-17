# core/interface/job_selection_process_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Optional
from core.entities.selection_process import JobSelectionProcess
from core.entities.selection_stage import SelectionStage

class JobSelectionProcessRepositoryPort(ABC):

    @abstractmethod
    def save_job_selection_process(self, job_id: int, stage_ids: List[int]) -> List[JobSelectionProcess]:
        """Save selection stages for a job"""
        raise NotImplementedError
    
    @abstractmethod
    def get_job_selection_processes(self, job_id: int) -> List[JobSelectionProcess]:
        """Get all selection process records for a job"""
        raise NotImplementedError
    
    @abstractmethod
    def get_job_selection_stages(self, job_id: int) -> List[SelectionStage]:
        """Get all selection stages for a job with details"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_job_selection_process(self, job_id: int) -> bool:
        """Delete all selection stages for a job"""
        raise NotImplementedError
    
    @abstractmethod
    def job_has_stages(self, job_id: int) -> bool:
        """Check if job has configured stages"""
        raise NotImplementedError
    
    @abstractmethod
    def update_stage_order(self, job_id: int, stage_id: int, new_order: int) -> Optional[JobSelectionProcess]:
        """Update the order of a specific stage for a job"""
        raise NotImplementedError