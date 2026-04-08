from subscription.models import UserSubscription, SubscriptionPlanModel
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserSubscriptionRepository:

    def get_by_user(self, user_id: int) -> UserSubscription | None:
        try:
            return UserSubscription.objects.select_related('plan').get(user_id=user_id)
        except UserSubscription.DoesNotExist:
            return None

    def get_by_stripe_session(self, session_id: str) -> UserSubscription | None:
        try:
            return UserSubscription.objects.get(stripe_checkout_session_id=session_id)
        except UserSubscription.DoesNotExist:
            return None

    def create_or_update_incomplete(self, user_id: int, plan_id: int, session_id: str, stripe_customer_id: str):
        sub, _ = UserSubscription.objects.update_or_create(
            user_id=user_id,
            defaults={
                'plan_id': plan_id,
                'stripe_checkout_session_id': session_id,
                'stripe_customer_id': stripe_customer_id,
                'status': 'incomplete',  # Not paid yet
            }
        )
        return sub

    def activate_subscription(
        self,
        user_id: int,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        plan_id: int,
        period_start: datetime,
        period_end: datetime,
    ):
        sub, _ = UserSubscription.objects.update_or_create(
            user_id=user_id,
            defaults={
                'plan_id': plan_id,
                'stripe_subscription_id': stripe_subscription_id,
                'stripe_customer_id': stripe_customer_id,
                'status': 'active',
                'current_period_start': period_start,
                'current_period_end': period_end,
                'canceled_at': None,
            }
        )
        logger.info(f"Activated subscription for user {user_id}")
        return sub

    def mark_canceled(self, stripe_subscription_id: str):
        UserSubscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).update(
            status='canceled',
            canceled_at=timezone.now()
        )
        logger.info(f"Marked subscription {stripe_subscription_id} as canceled")

    def mark_incomplete_expired(self, session_id: str):
        UserSubscription.objects.filter(
            stripe_checkout_session_id=session_id
        ).update(status='incomplete_expired')
        logger.info(f"Marked session {session_id} as incomplete_expired")

    def mark_past_due(self, stripe_subscription_id: str):
        UserSubscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).update(status='past_due')