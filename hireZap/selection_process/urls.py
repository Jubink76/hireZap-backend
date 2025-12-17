from django.urls import path
from .views import (
    CreateStageView,
    GetAllStagesView,
    GetStageById,
    UpdateStageView,
    DeleteStageView,
    GetInactiveStagesView,
    ReactivateStageView,
    SaveJobSelectionProcessView,
    GetJobSelectionProcessView
)

urlpatterns = [
    path('create-stage/',CreateStageView.as_view(),name='create-stage'),
    path('all-stages/',GetAllStagesView.as_view(), name='get-all-stages'),
    path('stage/<int:stage_id>',GetStageById.as_view(), name='get-stage-by-id'),
    path('update-stage/<int:stage_id>',UpdateStageView.as_view(), name='update-stage'),
    path('delete-stage/<int:stage_id>', DeleteStageView.as_view(), name='delete-stage'),
    path('stages/inactive/', GetInactiveStagesView.as_view(), name='get-inactive-stages'),
    path('stages/<int:stage_id>/reactivate/', ReactivateStageView.as_view(), name='reactivate-stage'),
    path('jobs/<int:job_id>/',GetJobSelectionProcessView.as_view(), name='get-job-selection-process'),
    path('jobs/<int:job_id>/save/',SaveJobSelectionProcessView.as_view(),name='save-job-selection-process'),
]