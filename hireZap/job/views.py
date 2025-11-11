from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from job.serializers import CreateJobSerializer

from core.use_cases.job.create_job import CreateJobUseCase
from core.use_cases.job.fetch_active_jobs import FetchActiveJobsUsecase
from core.use_cases.job.get_jobs_by_recruiter import GetJobsByRecruiterUsecase
from core.use_cases.job.get_all_jobs import GetAllJobsUsecase
from core.use_cases.job.get_all_inactive_jobs import GetInactiveJobsUsecase
from core.use_cases.job.get_all_paused_jobs import GetPausedJobsUsecase
from core.use_cases.job.get_job_by_id import GetJobBYIdUsecase
from infrastructure.repositories.job_repository import JobRepository

import logging
logger = logging.getLogger(__name__)

job_repo = JobRepository()
create_job_useCase = CreateJobUseCase(job_repo)
fetch_active_jobs_usecase = FetchActiveJobsUsecase(job_repo)
get_recrutir_jobs_usecase = GetJobsByRecruiterUsecase(job_repo)
get_all_jobs_usecase = GetAllJobsUsecase(job_repo)
get_inactive_jobs_usecase = GetInactiveJobsUsecase(job_repo)
get_paused_jobs_usecase = GetPausedJobsUsecase(job_repo)
get_job_by_id_usecase = GetJobBYIdUsecase(job_repo)

class CreateJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response(
                 {'error': 'Only recruiter can create jobs'},
                 status = status.HTTP_403_FORBIDDEN
            )
        serializer = CreateJobSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status= status.HTTP_400_BAD_REQUEST
            )

        company_id = request.data.get('company_id')
        if not company_id:
            return Response(
                {'error': 'Company Id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = create_job_useCase.execute(
                recruiter_id=request.user.id,
                company_id=company_id,
                job_data=serializer.validated_data
            )

            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    'message': result['message'],
                    'job': result['job']
                },
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetJobsByRecruiter(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            res = get_recrutir_jobs_usecase.execute(request.user.id)
            if not res['success']:

                return Response(
                    {'error': res.get('error', 'Failed to fetch jobs')},
                    status= status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(
                {'jobs' : res['jobs']},
                status = status.HTTP_200_OK
            )
        except Exception as e:

            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FetchActiveJobs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            res = fetch_active_jobs_usecase.execute()
            if not res['success']:
                return Response(
                    {'error': res.get('error', "Failed to fetch jobs")},
                    status = status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(
                {'jobs': res['jobs']},
                status= status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
class GetAllJobs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            res = get_all_jobs_usecase.excecute()
            if not res['success']:

                return Response(
                    {'error': res.get('error', 'Failed to fetch all jobs')},
                    status= status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(
                {'jobs' : res['jobs']},
                status = status.HTTP_200_OK
            )
        except Exception as e:

            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetInactiveJobs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            res = get_inactive_jobs_usecase.execute()
            if not res['success']:

                return Response(
                    {'error': res.get('error', 'Failed to fetch inactive jobs')},
                    status= status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(
                {'jobs' : res['jobs']},
                status = status.HTTP_200_OK
            )
        except Exception as e:

            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetPausedJobs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            res = get_paused_jobs_usecase.execute()
            if not res['success']:

                return Response(
                    {'error': res.get('error', 'Failed to fetch paused jobs')},
                    status= status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(
                {'jobs' : res['jobs']},
                status = status.HTTP_200_OK
            )
        except Exception as e:

            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetJobDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,job_id):
        try:
            res = get_job_by_id_usecase.execute(job_id)
            if not res['success']:
                return Response(
                    {'error': res.get('error','Failed to fetch job details')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            job_data = res['job']
            logger.debug(f"[API View] Full response payload: {job_data}")
            return Response(
                {'job': res['job']},
                status = status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

