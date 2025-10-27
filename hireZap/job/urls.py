from django.urls import path
from job.views import (
    CreateJobView
)
urlpatterns = [
    path('job/create-job/',CreateJobView.as_view(),name='create-job'),
]