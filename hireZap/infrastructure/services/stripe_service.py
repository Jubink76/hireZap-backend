import stripe
from django.conf import settings
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:

    def get_or_create_customer(self, user) -> str:
        from subscription.models import UserSubscription
        
        sub = UserSubscription.objects.filter(user=user).first()
        if sub and sub.stripe_customer_id:
            return sub.stripe_customer_id
        
        customer = stripe.Customer.create(
            email = user.email,
            name = getattr(user, 'full_name', user.email),
            metadata={'user_id':str(user.id)}
        )
        logger.info(f"created stripe customer {customer.id} for user {user.id}")
        return customer.id
    

    def create_checkout_session(self, user, stripe_price_id:str, plan_id:int) -> Dict:
        try:
            customer_id = self.get_or_create_customer(user)

            session =  stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'], 
                line_items=[{
                    'price':stripe_price_id,
                    'quantity':1
                }],
                mode='subscription',
                success_url=settings.STRIPE_SUCCESS_URL + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.STRIPE_CANCEL_URL,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan_id),
                },
                # Auto-expire incomplete sessions after 30 minutes
                expires_at=int(__import__('time').time()) + 1800,
            )
            logger.info(f"Created checkout session {session.id} for user {user.id}")
            return {'success': True, 'session_id': session.id, 'url': session.url}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating session: {str(e)}")
            return {'success': False, 'error': str(e)}
        
    def cancel_subscription(self, stripe_subscription_id: str) -> Dict:
        try:
            subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True
            )
            return {'success': True, 'subscription': subscription}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            return {'success': False, 'error': str(e)}

    def construct_webhook_event(self, payload: bytes, sig_header: str):
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )