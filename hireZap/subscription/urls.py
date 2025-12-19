from django.urls import path
from subscription.views import (
    CreatePlanView
)

urlpatterns = [
    path('create/plan/',CreatePlanView.as_view(), name='create-plan'),
]