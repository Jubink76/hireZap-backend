from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
from core.entities.subscription import SubscriptionPlan
from subscription.models import SubscriptionPlanModel
from typing import Optional, List
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class SubscriptionPlanRepository(SubscriptionPlanRepositoryPort):
    def create_plan(self, plan:SubscriptionPlan) -> SubscriptionPlan:
        """Create subscription plan"""
        plan_model = SubscriptionPlanModel.objects.create(
            name=plan.name,
            price=plan.price,
            period=plan.period,
            description=plan.description,
            features=plan.features,
            button_text=plan.button_text,
            card_color=plan.card_color,
            user_type=plan.user_type,
            badge=plan.badge,
            is_default=plan.is_default,
            is_free = plan.is_free,
            is_active=plan.is_active
        )

        return self._model_to_entity(plan_model)
    
    def get_all_plans(self, user_type:Optional[str]=None, include_inactive:bool=False) -> List[SubscriptionPlan]:
        """Get all subscription plans"""
        query = SubscriptionPlanModel.objects.all()
        
        if user_type:
            query = query.filter(user_type=user_type)
        if not include_inactive:
            query = query.filter(is_active=True)

        plans = query.order_by('price', 'created_at')
        return [self._model_to_entity(plan) for plan in plans]
    
    def get_plan_by_id(self,plan_id:int) -> SubscriptionPlan:
        """Get plan by id"""
        try:
            plan_model = SubscriptionPlanModel.objects.get(id=plan_id)
            return self._model_to_entity(plan_model)
        except SubscriptionPlanModel.DoesNotExist:
            return None
    
    def get_active_plans(self, user_type:str)-> List[SubscriptionPlan]:
        """Get all active plan for a user"""
        plans = SubscriptionPlanModel.objects.filter(
            user_type=user_type,
            is_active=True
        ).order_by('price', 'created_at')
        return [self._model_to_entity(plan) for plan in plans]
    
    def get_inactive_plans(self, user_type:Optional[str]=None) -> List[SubscriptionPlan]:
        """Get inactive plans"""
        query = SubscriptionPlanModel.objects.filter(is_active = False)

        if user_type:
            query = query.filter(user_type= user_type)
        plans = query.order_by('-updated_at')
        return [self._model_to_entity(plan) for plan in plans]
    
    
    def delete_plan(self,plan_id:int) -> bool:
        """Inactive plan by deleting"""
        try:
            plan_model = SubscriptionPlanModel.objects.get(id=plan_id)
            plan_model.is_active = False
            plan_model.save()
            return True
        except SubscriptionPlanModel.DoesNotExist:
            return False
    
    def update_plan(self, plan_id:int, plan_data:dict) -> Optional[SubscriptionPlan]:
        """Update subscription plan"""
        try:
            plan_model = SubscriptionPlanModel.objects.get(id=plan_id)

            for field, value in plan_data.items():
                if hasattr(plan_model, field):
                    setattr(plan_model, field, value)

            plan_model.save()
            return self._model_to_entity(plan_model)
        
        except SubscriptionPlanModel.DoesNotExist:
            return None
    
    def reactivate_plan(self,plan_id:int) -> Optional[SubscriptionPlan]:
        """Reactivate plan"""
        try:
            plan_model = SubscriptionPlanModel.objects.get(id=plan_id)
            if plan_model.is_active:
                return None
            plan_model.is_active = True
            plan_model.save()
            return self._model_to_entity(plan_model)
        except SubscriptionPlanModel.DoesNotExist:
            return None
        
    def _model_to_entity(self,model:SubscriptionPlanModel) -> SubscriptionPlan:
        """Convert model to entity"""
        return SubscriptionPlan(
            id=model.id,
            name=model.name,
            price=float(model.price),
            period=model.period,
            description=model.description,
            features=model.features,
            button_text=model.button_text,
            card_color=model.card_color,
            user_type=model.user_type,
            badge=model.badge,
            is_default=model.is_default,
            is_free=model.is_free,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )