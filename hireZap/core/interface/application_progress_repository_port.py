from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.entities.selection_stage import SelectionStage

class ApplicationProgressRepositoryPort(ABC):
    """Port for application progress repository"""
    
    @abstractmethod
    def get_application_by_id(self, application_id: int, candidate_id: int):
        """Get application by ID ensuring candidate ownership"""
        pass
    
    @abstractmethod
    def get_job_stages(self, job_id: int) -> List[SelectionStage]:
        """Get job's selection process stages ordered by sequence"""
        pass
    
    @abstractmethod
    def get_resume_screening_progress(self, application_id: int) -> Optional[Dict]:
        """Get resume screening progress for application"""
        pass
    
    @abstractmethod
    def get_telephonic_interview_progress(self, application_id: int) -> Optional[Dict]:
        """Get telephonic interview progress for application"""
        pass
    
    @abstractmethod
    def get_stage_history(self, application_id: int, stage_id: int) -> Optional[Dict]:
        """Get stage history for application"""
        pass