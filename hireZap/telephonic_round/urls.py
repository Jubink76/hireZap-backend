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
    EndCallAPIView,
    GetInterviewDetailsAPIView,
    ManualScoreOverrideAPIView,
    MoveToNextStageAPIView,
    GetInterviewStatsAPIView,
    AnalyzeInterviewAPIView,
)
urlpatterns = [
    # ================== SETTINGS ==================
    path('settings/<int:job_id>/',GetTelephonicSettingsAPIView.as_view(),name='get-settings'),
    path('settings/<int:job_id>/update/',UpdateTelephonicSettingsAPIView.as_view(),name='update-settings'),
    
    # ================== CANDIDATES ==================
    path('candidates/<int:job_id>/',GetTelephonicCandidatesAPIView.as_view(),name='get-candidates'),
    
    # Get statistics for telephonic round
    path('stats/<int:job_id>/',GetInterviewStatsAPIView.as_view(),name='get-stats'),
    
    # ================== SCHEDULING ==================

    path('schedule/',ScheduleInterviewAPIView.as_view(),name='schedule-interview'),
    
    # Bulk schedule multiple interviews
    path('bulk-schedule/',BulkScheduleInterviewsAPIView.as_view(),name='bulk-schedule-interviews'),
    path('reschedule/<int:interview_id>/',RescheduleInterviewAPIView.as_view(),name='reschedule-interview'),
    
    # ================== CALL MANAGEMENT ==================
    path('start-call/',StartCallAPIView.as_view(),name='start-call'),
    path('end-call/',EndCallAPIView.as_view(),name='end-call'),
    
    # ================== INTERVIEW DETAILS ==================
    path('details/<int:interview_id>/',GetInterviewDetailsAPIView.as_view(),name='get-interview-details'),
    
    # ================== SCORING & ANALYSIS ==================
    # Manually analyze interview (usually done automatically via Celery)
    path('analyze/<int:interview_id>/',AnalyzeInterviewAPIView.as_view(),name='analyze-interview'),
    
    # Override AI score with manual score
    path('manual-score/',ManualScoreOverrideAPIView.as_view(),name='manual-score-override'),
    
    # ================== STAGE PROGRESSION ==================
    # Move qualified candidates to next stage
    path('move-next-stage/',MoveToNextStageAPIView.as_view(),name='move-to-next-stage'),
]