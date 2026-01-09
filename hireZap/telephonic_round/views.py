from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import uuid

from .serializers import (
    TelephonicRoundSettingsSerializer,
    ScheduleInterviewSerializer,
    BulkScheduleSerializer,
    RescheduleInterviewSerializer,
    StartCallSerializer,
    EndCallSerializer,
    TelephonicInterviewSerializer,
    TelephonicCandidateListSerializer,
    ManualScoreOverrideSerializer,
    MoveToNextStageSerializer
)

from infrastructure.repositories.telephonic_round_repository import TelephonicRoundRepository
from infrastructure.services.notification_service import NotificationService
from infrastructure.services.storage_factory import StorageFactory
from infrastructure.services.telephonic_service import TranscriptionService,InterviewScorerService

from core.use_cases.telephonic_round.schedule_interview_usecase import ScheduleInterviewUsecase
from core.use_cases.telephonic_round.analyze_interview_usecase import AnalyzeInterviewUseCase
from core.use_cases.telephonic_round.bulk_schedule_usecase import BulkScheduleUseCase
from core.use_cases.telephonic_round.end_call_usecase import EndCallUseCase
from core.use_cases.telephonic_round.get_interview_details_usecase import GetInterviewDetailsUseCase
from core.use_cases.telephonic_round.manual_score_override_usecase import ManualScoreOverrideUseCase
from core.use_cases.telephonic_round.move_to_next_stage_usecase import MoveToNextStageUseCase
from core.use_cases.telephonic_round.reschedule_interview_usecase import RescheduleInterviewUseCase
from core.use_cases.telephonic_round.start_call_usecase import StartCallUseCase
from core.use_cases.telephonic_round.get_telephonic_round_settings_usecase import GetTelephonicRoundSettings
from core.use_cases.telephonic_round.update_settings_usecase import UpdateSettingsUseCase
from core.use_cases.telephonic_round.get_stats_usecase import GetStatsUsecase
from core.use_cases.telephonic_round.get_telephonic_round_candidates import GetTelephonicRoundCandidates
from .tasks import process_interview_recording_task


class GetTelephonicSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            # Execute use case
            use_case = GetTelephonicRoundSettings(repository)
            result = use_case.execute(job_id)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateTelephonicSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, job_id):
        try:
            # Validate input
            serializer = TelephonicRoundSettingsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            # Execute use case
            use_case = UpdateSettingsUseCase(repository)
            result = use_case.execute(job_id, serializer.validated_data)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class GetTelephonicCandidatesAPIView(APIView):
    """Get all candidates for telephonic round of a job"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            # Get optional status filter from query params
            status_filter = request.query_params.get('status', None)
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            # Execute use case
            use_case = GetTelephonicRoundCandidates(repository)
            result = use_case.execute(job_id, status_filter)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleInterviewAPIView(APIView):
    """Schedule single interview"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = ScheduleInterviewSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = ScheduleInterviewUsecase(repository, notification_service)
            result = use_case.execute(
                application_id=data['candidate_id'],
                scheduled_at=data['scheduled_at'],
                duration=data.get('duration', 30),
                timezone=data.get('timezone', 'America/New_York'),
                notes=data.get('notes', ''),
                send_notification=data.get('send_notification', True),
                send_email=data.get('send_email', True)
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkScheduleInterviewsAPIView(APIView):
    """Bulk schedule interviews"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = BulkScheduleSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = BulkScheduleUseCase(repository, notification_service)
            result = use_case.execute(
                schedules=serializer.validated_data['schedules'],
                send_notifications=request.data.get('send_notifications', True),
                send_emails=request.data.get('send_emails', True)
            )
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RescheduleInterviewAPIView(APIView):
    """Reschedule an existing interview"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, interview_id):
        try:
            # Validate input
            serializer = RescheduleInterviewSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = RescheduleInterviewUseCase(repository, notification_service)
            result = use_case.execute(
                interview_id=interview_id,
                new_scheduled_at=data['scheduled_at'],
                duration=data.get('duration'),
                timezone=data.get('timezone'),
                notes=data.get('notes'),
                send_notification=data.get('send_notification', True),
                send_email=data.get('send_email', True)
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StartCallAPIView(APIView):
    """Start telephonic interview call"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = StartCallSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            interview_id = serializer.validated_data['interview_id']
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = StartCallUseCase(repository, notification_service)
            result = use_case.execute(
                interview_id=interview_id,
                recruiter_id=request.user.id
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EndCallAPIView(APIView):
    """End call and upload recording"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = EndCallSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Get recording file if provided
            recording_file = request.FILES.get('recording_file', None)
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            storage = StorageFactory.get_default_storage()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = EndCallUseCase(repository, storage, notification_service)
            result = use_case.execute(
                session_id=data['call_session_id'],
                duration_seconds=data['duration_seconds'],
                recording_file=recording_file,
                connection_quality=data.get('connection_quality', 'good')
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetInterviewDetailsAPIView(APIView):
    """Get detailed interview results"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interview_id):
        try:
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            
            # Execute use case
            use_case = GetInterviewDetailsUseCase(repository)
            result = use_case.execute(interview_id, request.user.id)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_404_NOT_FOUND if 'not found' in result.get('error', '').lower() else status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManualScoreOverrideAPIView(APIView):
    """Override AI score with manual score"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = ManualScoreOverrideSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = ManualScoreOverrideUseCase(repository, notification_service)
            result = use_case.execute(
                interview_id=data['interview_id'],
                manual_score=data['manual_score'],
                manual_decision=data['manual_decision'],
                override_reason=data['override_reason'],
                overridden_by_id=request.user.id
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MoveToNextStageAPIView(APIView):
    """Move qualified candidates to next stage"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = MoveToNextStageSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = MoveToNextStageUseCase(repository, notification_service)
            result = use_case.execute(
                interview_ids=data['interview_ids'],
                feedback=data.get('feedback', 'Passed telephonic round')
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetInterviewStatsAPIView(APIView):
    """Get statistics for telephonic round"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            
            # Execute use case
            use_case = GetStatsUsecase(repository)
            result = use_case.execute(job_id)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyzeInterviewAPIView(APIView):
    """
    Manually trigger interview analysis
    (Usually done automatically via Celery after call ends)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, interview_id):
        try:
            audio_file_path = request.data.get('audio_file_path')
            
            if not audio_file_path:
                return Response({
                    'success': False,
                    'error': 'audio_file_path is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize dependencies
            repository = TelephonicRoundRepository()
            transcription_service = TranscriptionService()
            scorer_service = InterviewScorerService()
            notification_service = NotificationService()
            
            # Execute use case
            use_case = AnalyzeInterviewUseCase(
                repository,
                transcription_service,
                scorer_service,
                notification_service
            )
            result = use_case.execute(interview_id, audio_file_path)
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)