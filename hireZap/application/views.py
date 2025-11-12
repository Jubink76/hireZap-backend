from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from application.serializers import (
    ApplicationSerializer,
    UpdateApplicationStatusSerializer
)

from infrastructure.repositories.application_repository import ApplicationRepository

from core.use_cases.application.create_application_usecase import CreateApplicationUsecase
from core.use_cases.application.get_application_usecase import GetApplicationByIdUsecase
from core.use_cases.application.get_application_by_candidate_usecase import GetApplicationByCandidateUsecase
from core.use_cases.application.get_application_by_job_usecase import GetApplicationByJobUsecase
from core.use_cases.application.update_application_status_usecase import UpdateApplicationStatusUsecase
from core.use_cases.application.withdraw_application_usecase import WithdrawApplicationUsecase
from core.use_cases.application.check_application_exist_usecase import CheckApplicationExistsUseCase
from core.use_cases.application.get_application_statics_usecase import GetApplicationStatisticsUsecase

app_repo = ApplicationRepository()
create_application_usecase = CreateApplicationUsecase(app_repo)
get_application_by_id_usecase = GetApplicationByIdUsecase(app_repo)
get_candidate_application_usecase = GetApplicationByCandidateUsecase(app_repo)
get_application_by_job_usecase = GetApplicationByJobUsecase(app_repo)
update_application_status_usecase = UpdateApplicationStatusUsecase(app_repo)
withdraw_application_usecase = WithdrawApplicationUsecase(app_repo)
check_application_exist_usecase = CheckApplicationExistsUseCase(app_repo)
get_application_statistics_usecase = GetApplicationStatisticsUsecase(app_repo)

import logging
logger = logging.getLogger(__name__)

class CreateApplicationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        """ create or save draft application """
        try:
            serializer = ApplicationSerializer(data= request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        'success':False,
                        'error':"Invalid data",
                        'details':serializer.errors
                    },
                    status= status.HTTP_400_BAD_REQUEST
                )
            application_data = serializer.validated_data
            application_data['candidate_id'] = request.user.id
            
            result = create_application_usecase.execute(application_data)
            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(result,status=status.HTTP_201_CREATED)
        except Exception as e:
                    return Response({
                        'success': False,
                        'error': str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,application_id):
        try:
            result = get_application_by_id_usecase.execute(application_id)
            if not result['success']:
                return Response(
                    {'error':result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(result,status= status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CandidateApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            include_drafts = request.query_params.get('include_drafts', 'false').lower() == 'true'
            result = get_candidate_application_usecase.execute(request.user.id,include_drafts)
            if not result['success']:
                return Response({
                    'error':result['error']
                }, status = status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class JobApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request, job_id):
        try:
            if not request.user.is_recruiter:
                return Response(
                    {
                        'success':False,
                        'error':"Only recruiter can view job applications"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            status_filter = request.query_params.get('status',None)
            result = get_application_by_job_usecase.execute(job_id,status_filter)
            if not result['success']:
                return Response({
                    'error':result['error'],
                },status=status.HTTP_400_BAD_REQUEST)
            return Response(result,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateApplicationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request,application_id):
        try:
            if not request.user.is_recruiter:
                return Response(
                    {'success':False,
                     'error':"Only recruiter can update status"},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = UpdateApplicationStatusSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        'success':False,
                        'error':'Invalid data',
                        'details':serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            new_status = serializer.validated_data('status')
            result = update_application_status_usecase.execute(application_id,new_status)
            if not result['success']:
                return Response(
                    {'error':result['error']},
                    status = status.HTTP_400_BAD_REQUEST
                )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WithdrawApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,application_id):

        try:
            result = withdraw_application_usecase.execute(request.user.id,application_id)
            if not result['success']:
                return Response({
                    'error':result['error']
                },status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckApplicationExistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,job_id):
        """Check if user has already applied or has a draft for this job"""
        try:
            result = check_application_exist_usecase.execute(job_id,request.user.id)
            if not result['success']:
                return Response({
                    'error':result['error']
                },status=status.HTTP_400_BAD_REQUEST)
            return Response(result,status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetApplicationStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,job_id):
        """Get application statistics for a job (recruiter only)"""
        try:
            if not request.user.is_recruiter:
                return Response({
                    'success': False,
                    'error': 'Only recruiters can view application statistics'
                }, status=status.HTTP_403_FORBIDDEN)

            result = get_application_statistics_usecase.execute(job_id)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




          