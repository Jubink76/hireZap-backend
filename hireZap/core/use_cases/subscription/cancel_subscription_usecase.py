from infrastructure.services.stripe_service import StripeService
from infrastructure.repositories.user_subscription_repository import UserSubscriptionRepository
import logging

logger = logging.getLogger(__name__)


class CancelSubscriptionUseCase:
    def __init__(self):
        self.stripe_service = StripeService()
        self.sub_repo = UserSubscriptionRepository()

    def execute(self, user_id: int) -> dict:
        try:
            subscription = self.sub_repo.get_by_user(user_id)
            if not subscription:
                return {'success': False, 'error': 'No active subscription found'}

            if subscription.status != 'active':
                return {'success': False, 'error': f'Subscription is already {subscription.status}'}

            result = self.stripe_service.cancel_subscription(subscription.stripe_subscription_id)
            if not result['success']:
                return result

            # Access remains until period end — Stripe webhook handles final status update
            return {
                'success': True,
                'message': 'Subscription will be canceled at end of billing period',
                'ends_at': subscription.current_period_end.isoformat()
            }

        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return {'success': False, 'error': str(e)}