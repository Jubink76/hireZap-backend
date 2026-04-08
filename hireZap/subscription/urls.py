from django.urls import path
from subscription.views import (
    CreatePlanView,
    GetAllPlanView,
    UpdatePlanView,
    DeletePlanView,
    ReactivatePlanView,
    GetInactivePlanView,
)
from subscription.payment_views import CreateCheckoutSessionView, CancelSubscriptionView, MySubscriptionView
from subscription.webhook_views import StripeWebhookView

urlpatterns = [
    path('create/plan/',CreatePlanView.as_view(), name='create-plan'),
    path('plans/',GetAllPlanView.as_view(), name='get-all-plans'),
    path('plans/<int:plan_id>/update/',UpdatePlanView.as_view(), name='update-plan'),
    path('plans/<int:plan_id>/delete/',DeletePlanView.as_view(), name='delete-plan'),
    path('plans/<int:plan_id>/reactivate/',ReactivatePlanView.as_view(), name='reactivate-plan'),
    path('plans/inactive/',GetInactivePlanView.as_view(), name='get-inactive-plans'),

    path('subscribe/<int:plan_id>/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/me/', MySubscriptionView.as_view(), name='my-subscription'),
    # Webhook — must be excluded from authentication middleware
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
]