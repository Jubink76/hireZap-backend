from django.urls import path
from resume_screening.views import (
    ATSConfigureView,
    StartBUlkScreeningView,
    GetScreeningProgressView,
    GetScreeningResultsView,
    MoveToNextStageView,
    PauseScreeningView,
    ResetScreeningView
)
urlpatterns = [
    path('jobs/<int:job_id>/ats-config/', ATSConfigureView.as_view(), name='ats-config'),
    path('jobs/<int:job_id>/start-bulk-screening/', StartBUlkScreeningView.as_view(), name='start-bulk-screening'),
    path('jobs/<int:job_id>/screening-progress/',GetScreeningProgressView.as_view(),name='screening-progress'),
    path('jobs/<int:job_id>/screening-results/', GetScreeningResultsView.as_view(),name='screening-results'),
    path('applications/move-to-next-stage/',MoveToNextStageView.as_view(), name='move-to-next-stage'),
    path('jobs/<int:job_id>/pause-screening/',PauseScreeningView.as_view(), name='pause-screening'),
    path('jobs/<int:job_id>/reset-screening/', ResetScreeningView.as_view(), name='reset-screening'),
]