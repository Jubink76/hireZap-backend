from django.urls import path
from subscription.views import (
    CreatePlanView,
    GetAllPlanView,
    UpdatePlanView,
    DeletePlanView,
    ReactivatePlanView,
    GetInactivePlanView,
)

urlpatterns = [
    path('create/plan/',CreatePlanView.as_view(), name='create-plan'),
    path('plans/',GetAllPlanView.as_view(), name='get-all-plans'),
    path('plans/<int:plan_id>/update/',UpdatePlanView.as_view(), name='update-plan'),
    path('plans/<int:plan_id>/delete/',DeletePlanView.as_view(), name='delete-plan'),
    path('plans/<int:plan_id>/reactivate/',ReactivatePlanView.as_view(), name='reactivate-plan'),
    path('plans/inactive/',GetInactivePlanView.as_view(), name='get-inactive-plans'),
]