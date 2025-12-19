from abc import ABC, abstractmethod
from typing  import List, Optional
from core.entities.subscription import SubscriptionPlan


class SubscriptionPlanRepositoryPort(ABC):
    @abstractmethod
    def create_plan(self, plan:SubscriptionPlan) -> SubscriptionPlan:
        """Create new subscription plan"""
        raise NotImplementedError
    
    
    
    