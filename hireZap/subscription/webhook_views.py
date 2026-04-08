import stripe
from django.views import View
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime

from infrastructure.repositories.user_subscription_repository import UserSubscriptionRepository
from infrastructure.repositories.subscription_plan_repository import SubscriptionPlanRepository
import logging

logger = logging.getLogger(__name__)
sub_repo = UserSubscriptionRepository()
plan_repo = SubscriptionPlanRepository()


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            from infrastructure.services.stripe_service import StripeService
            event = StripeService().construct_webhook_event(payload, sig_header)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook signature failed: {str(e)}")
            return HttpResponseBadRequest("Invalid signature")

        event_type = event['type']
        data = event['data']['object']

        logger.info(f"Stripe webhook received: {event_type}")

        handlers = {
            # ✅ Payment succeeded — activate subscription
            'checkout.session.completed': self._handle_checkout_completed,
            # ✅ Recurring payment succeeded — renew period
            'invoice.payment_succeeded': self._handle_payment_succeeded,
            # ❌ Payment failed (card declined etc.)
            'invoice.payment_failed': self._handle_payment_failed,
            # ❌ User abandoned checkout (30 min timeout)
            'checkout.session.expired': self._handle_checkout_expired,
            # 🔴 Subscription fully canceled
            'customer.subscription.deleted': self._handle_subscription_deleted,
            # ⚠️ Subscription updated (e.g. cancel_at_period_end set)
            'customer.subscription.updated': self._handle_subscription_updated,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(data)
        else:
            logger.debug(f"Unhandled webhook event: {event_type}")

        return HttpResponse(status=200)

    def _handle_checkout_completed(self, session):
        """Payment successful — activate the subscription"""
        user_id = int(session['metadata']['user_id'])
        plan_id = int(session['metadata']['plan_id'])
        stripe_subscription_id = session.get('subscription')
        stripe_customer_id = session.get('customer')

        # Fetch subscription details from Stripe for period dates
        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        period_start = datetime.fromtimestamp(stripe_sub['current_period_start'], tz=timezone.utc)
        period_end = datetime.fromtimestamp(stripe_sub['current_period_end'], tz=timezone.utc)

        sub_repo.activate_subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            plan_id=plan_id,
            period_start=period_start,
            period_end=period_end,
        )
        logger.info(f"✅ Subscription activated for user {user_id}")

    def _handle_payment_succeeded(self, invoice):
        """Recurring renewal — update period end date"""
        stripe_subscription_id = invoice.get('subscription')
        if not stripe_subscription_id:
            return

        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        period_end = datetime.fromtimestamp(stripe_sub['current_period_end'], tz=timezone.utc)

        from subscription.models import UserSubscription
        UserSubscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).update(
            status='active',
            current_period_end=period_end
        )
        logger.info(f"♻️ Subscription renewed: {stripe_subscription_id}")

    def _handle_payment_failed(self, invoice):
        """Card declined / payment failed — mark past_due"""
        stripe_subscription_id = invoice.get('subscription')
        if stripe_subscription_id:
            sub_repo.mark_past_due(stripe_subscription_id)
            logger.warning(f"⚠️ Payment failed for subscription {stripe_subscription_id}")

    def _handle_checkout_expired(self, session):
        """User abandoned checkout without paying"""
        session_id = session.get('id')
        sub_repo.mark_incomplete_expired(session_id)
        logger.info(f"🕐 Checkout session expired (abandoned): {session_id}")

    def _handle_subscription_deleted(self, subscription):
        """Subscription fully ended"""
        sub_repo.mark_canceled(subscription['id'])
        logger.info(f"🔴 Subscription deleted: {subscription['id']}")

    def _handle_subscription_updated(self, subscription):
        """Handles cancel_at_period_end being set to True"""
        if subscription.get('cancel_at_period_end'):
            from subscription.models import UserSubscription
            UserSubscription.objects.filter(
                stripe_subscription_id=subscription['id']
            ).update(status='canceled')  # Will lose access at period end
            logger.info(f"📅 Subscription set to cancel at period end: {subscription['id']}")