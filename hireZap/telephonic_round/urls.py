from django.urls import path
from django.urls import path
from .views import (
    GetTelephonicSettingsAPIView,
    UpdateTelephonicSettingsAPIView,
    GetTelephonicCandidatesAPIView,
    ScheduleInterviewAPIView,
    BulkScheduleInterviewsAPIView,
    RescheduleInterviewAPIView,
    StartCallAPIView,
    JoinCallAPIView,
    EndCallAPIView,
    GetInterviewDetailsAPIView,
    ManualScoreOverrideAPIView,
    MoveToNextStageAPIView,
    GetInterviewStatsAPIView,
    AnalyzeInterviewAPIView,
)
urlpatterns = [
    path('settings/<int:job_id>/',GetTelephonicSettingsAPIView.as_view(),name='get-settings'),
    path('settings/<int:job_id>/update/',UpdateTelephonicSettingsAPIView.as_view(),name='update-settings'),
    path('candidates/<int:job_id>/',GetTelephonicCandidatesAPIView.as_view(),name='get-candidates'),
    path('stats/<int:job_id>/',GetInterviewStatsAPIView.as_view(),name='get-stats'),
    path('schedule/',ScheduleInterviewAPIView.as_view(),name='schedule-interview'),
    path('bulk-schedule/',BulkScheduleInterviewsAPIView.as_view(),name='bulk-schedule-interviews'),
    path('reschedule/<int:interview_id>/',RescheduleInterviewAPIView.as_view(),name='reschedule-interview'),
    path('start-call/',StartCallAPIView.as_view(),name='start-call'),
    path('join-call/',JoinCallAPIView.as_view(), name='join-call'),
    path('end-call/',EndCallAPIView.as_view(),name='end-call'),
    path('details/<int:interview_id>/',GetInterviewDetailsAPIView.as_view(),name='get-interview-details'),
    path('analyze/<int:interview_id>/',AnalyzeInterviewAPIView.as_view(),name='analyze-interview'),
    path('manual-score/',ManualScoreOverrideAPIView.as_view(),name='manual-score-override'),
    path('move-next-stage/',MoveToNextStageAPIView.as_view(),name='move-to-next-stage'),
]