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
    def get_by_id(self, user_id:int) -> Optional[UserEntity]:
        """ Return user by Id """
        raise NotImplementedError
    
    @abstractmethod
    def authenticate(self,email:str, password:str) -> Optional[UserEntity]:
        """ return user if credentials are valid or None"""
        raise NotImplementedError
    
    @abstractmethod
    def update_last_login(self,user_id:str):
        """ update last login using timestamp"""
        raise NotImplementedError
    
    @abstractmethod
    def update_password(self,email:str, new_passowrd:str) -> bool:
        """ update user password and return true"""
        raise NotImplementedError
    
    @abstractmethod
    def update_user_profile(self, user_id:int, user_entity:UserEntity) -> UserEntity:
        """ Update uer profile and reutrn updated user """
        raise NotImplementedError
    
    @abstractmethod
    def email_exists_for_other_user(self,email:str, user_id:int) -> bool:
        """ Check if the email is used by another user (excluding current user) """
        raise NotImplementedError