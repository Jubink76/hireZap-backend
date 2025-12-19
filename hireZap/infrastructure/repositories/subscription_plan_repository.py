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
            is_active=plan.is_active
        )

        return self._model_to_entity(plan_model)
    
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
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )