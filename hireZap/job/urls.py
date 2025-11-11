from django.urls import path
from job.views import (
    CreateJobView,
    FetchActiveJobs,
    GetJobsByRecruiter,
    GetAllJobs,
    GetInactiveJobs,
    GetPausedJobs,
    GetJobDetail
)
urlpatterns = [
    path('create-job/',CreateJobView.as_view(),name='create-job'),
    path('fetch/active-jobs/',FetchActiveJobs.as_view(),name='fetch-active-jobs'),
    path('created-jobs/',GetJobsByRecruiter.as_view(),name='recruiter-created-jobs'),
    path('fetch/all-jobs/',GetAllJobs.as_view(),name='fetch-all-jobs'),
    path('fetch/inactive-jobs/',GetInactiveJobs.as_view(),name='fetch-inactive-jobs'),
    path('fetch/paused-jobs/',GetPausedJobs.as_view(),name='fetch-paused-jobs'),
    path('fetch/job-detail/<int:job_id>/',GetJobDetail.as_view(),name='fetch-job-detail')
    
]