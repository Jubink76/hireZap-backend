from django.urls import path
from admin.views import(
    AdminDashboardView,
    AdminCandidatesListView,
    AdminCandidateDetailView,
    AdminCandidateSearchView,
    AdminRecruitersListView,
    AdminRecruiterDetailView,
    AdminJobsListView,
    AdminJobDetailView,
    AdminApplicationsListView,
    AdminApplicationDetailView
)

urlpatterns = [
    path('dashboard/',AdminDashboardView.as_view(),name='admin-dashboard'),
    # candidates
    path('candidates/',AdminCandidatesListView.as_view(),name='admin-candidates-list'),
    path('candidates/search/', AdminCandidateSearchView.as_view(), name='admin-candidates-search'),
    path('candidates/<int:user_id>/', AdminCandidateDetailView.as_view(), name='admin-candidate-detail'),
    # Recruiters
    path('recruiters/', AdminRecruitersListView.as_view(), name='admin-recruiters-list'),
    path('recruiters/<int:user_id>/', AdminRecruiterDetailView.as_view(), name='admin-recruiter-detail'),
    
    # Jobs
    path('jobs/', AdminJobsListView.as_view(), name='admin-jobs-list'),
    path('jobs/<int:job_id>/', AdminJobDetailView.as_view(), name='admin-job-detail'),
    
    # Applications
    path('applications/', AdminApplicationsListView.as_view(), name='admin-applications-list'),
    path('applications/<int:application_id>/', AdminApplicationDetailView.as_view(), name='admin-application-detail'),
]