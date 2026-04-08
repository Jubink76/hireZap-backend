from infrastructure.services.stripe_service import StripeService
from infrastructure.repositories.user_subscription_repository import UserSubscriptionRepository
from infrastructure.repositories.subscription_plan_repository import SubscriptionPlanRepository
import logging

logger = logging.getLogger(__name__)


class CreateCheckoutSessionUseCase:
    def __init__(self):
        self.stripe_service = StripeService()
        self.sub_repo = UserSubscriptionRepository()
        self.plan_repo = SubscriptionPlanRepository()

    def execute(self, user, plan_id: int) -> dict:
        try:
            plan = self.plan_repo.get_plan_by_id(plan_id)
            if not plan:
                return {'success': False, 'error': 'Plan not found'}

            if plan.is_free:
                return {'success': False, 'error': 'Free plan does not require payment'}

            if not plan.stripe_price_id:
                return {'success': False, 'error': 'This plan is not configured for payment yet'}

            result = self.stripe_service.create_checkout_session(
                user=user,
                stripe_price_id=plan.stripe_price_id,
                plan_id=plan_id,
            )

            if not result['success']:
                return result

            # Save as 'incomplete' immediately — tracks abandoned payments
            self.sub_repo.create_or_update_incomplete(
                user_id=user.id,
                plan_id=plan_id,
                session_id=result['session_id'],
                stripe_customer_id=self.stripe_service.get_or_create_customer(user),
            )

            return {
                'success': True,
                'checkout_url': result['url'],
                'session_id': result['session_id'],
            }

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return {'success': False, 'error': str(e)}