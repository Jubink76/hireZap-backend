from django.urls import path
from application.views import(
    CreateApplicationView,
    ApplicationDetailView,
    CandidateApplicationView,
    JobApplicationView,
    UpdateApplicationStatusView,
    WithdrawApplicationView,
    GetApplicationStatisticsView,
    CheckApplicationExistView
)
urlpatterns = [
    path('apply/',CreateApplicationView.as_view(),name='create-application'),
    path('detail/<int:application_id>/',ApplicationDetailView.as_view(),name='application_datail'),
    path('my-applications/',CandidateApplicationView.as_view(),name=('my-applications')),
    path('list/job/<int:job_id>/',JobApplicationView.as_view(),name='job-applications'),
    path('update/<int:application_id>/status/',UpdateApplicationStatusView.as_view(),name='update-application-status'),
    path('withdraw/<int:application_id>/',WithdrawApplicationView.as_view(),name='withdraw-application'),
    path('check/<int:job_id>/',CheckApplicationExistView.as_view(),name='check-application'),
    path('job/<int:job_id>/statistics/',GetApplicationStatisticsView.as_view(),name='application-statistics'),
    
]