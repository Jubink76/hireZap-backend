from abc import ABC, abstractmethod
from core.entities.user import UserEntity
from typing import Optional

class AuthRepositoryPort(ABC):

    @abstractmethod
    def create(self, user:UserEntity):
        """ create and persist a user , return a representation"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_email(self, email:str):
        """ return user (or None ) by email"""
        raise NotImplementedError
    
    @abstractmethod
    def authenticate(self,email:str, password:str) -> Optional[UserEntity]:
        """ return user if credentials are valid or None"""
        raise NotImplementedError
    
    @abstractmethod
    def update_last_login(self,user_id:str):
        """ update last login using timestamp"""
        raise NotImplementedError