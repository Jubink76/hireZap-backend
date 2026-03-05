from abc import ABC, abstractmethod
from typing import Optional, List
from offer.models import OfferLetterModel


class OfferRepositoryPort(ABC):

    @abstractmethod
    def create_and_send_offer(self, application_id:int, data:dict, sent_by_user_id:int) -> OfferLetterModel:
        """Create and sent offer"""
        return NotImplementedError
    
    @abstractmethod
    def get_offer_by_id(self, offer_id:int) -> Optional[OfferLetterModel]:
        """Get offer by id"""
        return NotImplementedError
    
    @abstractmethod
    def get_offer_by_application(self, application_id:int) -> Optional[OfferLetterModel]:
        """Get offer by application"""
        return NotImplementedError
    
    @abstractmethod
    def candidate_respond(self, offer_id:int, action:str, note:str=None)->OfferLetterModel:
        """Candidate repsond to offer letter"""
        return NotImplementedError
    
    @abstractmethod
    def get_candidate_by_rank(self, job_id:int) -> List[dict]:
        """Get candidates based on the average of previous stage score"""
        return NotImplementedError
    
    