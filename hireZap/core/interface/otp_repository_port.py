from abc import ABC, abstractmethod
from core.entities.otp import OtpEntity


class OtpRepositoryPort(ABC):

    @abstractmethod
    def save_otp(self, otp:OtpEntity):
        """ save otp entry """
        raise NotImplementedError
    
    @abstractmethod
    def get_otp(self, email:str, action_type:str) -> OtpEntity | None:
        """ Fetch otp for a given email """
        raise NotImplementedError
    
    @abstractmethod
    def mark_verified(self, email:str, action_type:str):
        """ mark otp as verified"""
        raise NotImplementedError
