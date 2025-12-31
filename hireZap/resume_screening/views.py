from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.use_cases.resume_screening.configure_ats import (
    ConfigureATSUsecase,
    GetATSConfigUsecase
)
from core.use_cases.resume_screening.bulk_screening_usecase import StartBulkScreeningUseCase
from core.use_cases.resume_screening.get_screening_progress_usecase import GetScreeningProgressUseCase
from core.use_cases.resume_screening.get_screening_results_usecase import GetScreeningResultsUseCase
from core.use_cases.resume_screening.move_to_next_stage_usecase import MoveToNextStageUseCase

from infrastructure.repositories.ats_configuration_repository import ATSConfigRepository
from infrastructure.repositories.resume_screening_repository import ResumeScreeningRepository
from infrastructure.services.notification_service import NotificationService
from infrastructure.repositories.job_repository import JobRepository


import logging
logger = logging.getLogger(__name__)
ats_repo = ATSConfigRepository()
screening_repo = ResumeScreeningRepository()
notification_service = NotificationService()

class ATSConfigureView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request,job_id):
        """Configure ATS for a job"""
        usecase = ConfigureATSUsecase(
            job_repository=JobRepository(),
            ats_repository=ATSConfigRepository()
        )

        result = usecase.execute(job_id, request.data)
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self,request,job_id):
        """Get ATS configuration"""
        usecase = GetATSConfigUsecase(
            ats_repository=ATSConfigRepository()
        )
        
        result = usecase.execute(job_id)
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)

class StartBUlkScreeningView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request, job_id):
        usecase = StartBulkScreeningUseCase(
            screening_repo=ResumeScreeningRepository(),
            ats_repo=ATSConfigRepository()
        )
        result = usecase.execute(job_id)
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
class GetScreeningProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,job_id):
        usecase = GetScreeningProgressUseCase(
            screening_repo=ResumeScreeningRepository()
        )
        
        result = usecase.execute(job_id)
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result,status=status.HTTP_404_NOT_FOUND)

class GetScreeningResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        filters = {}
        if request.query_params.get('decision'):
            filters['decision'] = request.query_params.get('decision')
        if request.query_params.get('min_score'):
            filters['min_score'] = int(request.query_params.get('min_score'))
        if request.query_params.get('max_score'):
            filters['max_score'] = int(request.query_params.get('max_score'))
        usecase = GetScreeningResultsUseCase(
            screening_repo=ResumeScreeningRepository()
        )
        
        result = usecase.execute(job_id, filters if filters else None)
        if result['success']:
            return Response(result , status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
class MoveToNextStageView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        application_ids = request.data.get('application_ids',[])
        feedback = request.data.get('feedback')
        if not application_ids:
            return Response(
                {'success': False, 'error': 'No applications provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        usecase = MoveToNextStageUseCase(
            screening_repo=ResumeScreeningRepository(),
            notification_service=NotificationService()
        )
        
        result = usecase.execute(application_ids, feedback)
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
class PauseScreeningView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request, job_id):
        try:
            job = screening_repo.get_job_by_id(job_id)
            if not job:
                    return Response(
                        {'success': False, 'error': 'Job not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
            if job.screening_status != 'in_progress':
                return Response(
                    {'success': False, 'error': 'No screening in progress'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            screening_repo.update_job_screening_status(job_id, 'paused')
            return Response({
                    'success': True,
                    'message': 'Screening paused (running tasks will complete)'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
