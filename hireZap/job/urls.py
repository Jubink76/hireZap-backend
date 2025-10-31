from django.urls import path
from job.views import (
    CreateJobView,
    FetchActiveJobs,
    GetJobsByRecruiter
)
urlpatterns = [
    path('create-job/',CreateJobView.as_view(),name='create-job'),
    path('fetch/active-jobs/',FetchActiveJobs.as_view(),name='fetch-active-jobs'),
    path('created-jobs/',GetJobsByRecruiter.as_view(),name='recruiter-created-jobs'),
    
]