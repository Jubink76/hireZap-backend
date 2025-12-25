from abc import ABC, abstractmethod
from typing  import List, Optional
from core.entities.subscription import SubscriptionPlan


class SubscriptionPlanRepositoryPort(ABC):
    @abstractmethod
    def create_plan(self, plan:SubscriptionPlan) -> SubscriptionPlan:
        """Create new subscription plan"""
        raise NotImplementedError
    
    @abstractmethod
    def get_plan_by_id(self, plan_id:int) -> SubscriptionPlan:
        """Get plan by plan Id"""
        raise NotImplementedError
    
    @abstractmethod
    def get_all_plans(self, user_type:Optional[str]=None, include_inactive: bool = False) -> List[SubscriptionPlan]:
        """Get all subscription plans, Optionally filtered by user type"""
        raise NotImplementedError
    
    @abstractmethod
    def get_active_plans(self, user_type:str) -> List[SubscriptionPlan]:
        """Get active plans for a user type"""
        raise NotImplementedError
    
    @abstractmethod
    def get_inactive_plans(self,user_type:Optional[str]=None) -> List[SubscriptionPlan]:
        """Get only inactive plans"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_plan(self,plan_id:int) -> bool:
        """Inactive plan by deleting"""
        raise NotImplementedError
    
    @abstractmethod
    def update_plan(self,plan_id:int, plan_data:dict) -> Optional[SubscriptionPlan]:
        """Update existing plan"""
        raise NotImplementedError
    
    @abstractmethod
    def reactivate_plan(self,plan_id:int) -> Optional[SubscriptionPlan]:
        """Reactivate inactive plan"""
        raise NotImplementedError
    
    

    
    
    
    