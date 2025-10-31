from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from job.serializers import CreateJobSerializer

from core.use_cases.job.create_job import CreateJobUseCase
from core.use_cases.job.fetch_active_jobs import FetchActiveJobsUsecase
from core.use_cases.job.get_jobs_by_recruiter import GetJobsByRecruiterUsecase
from infrastructure.repositories.job_repository import JobRepository

import logging
logger = logging.getLogger(__name__)

job_repo = JobRepository()
create_job_useCase = CreateJobUseCase(job_repo)
fetch_active_jobs_usecase = FetchActiveJobsUsecase(job_repo)
get_recrutir_jobs_usecase = GetJobsByRecruiterUsecase(job_repo)

class CreateJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"📥 Job creation request from user: {request.user.id}")
        logger.debug(f"📦 Request data: {request.data}")
        if request.user.role != 'recruiter':
            logger.warning(f"⚠️ Non-recruiter user {request.user.id} tried to create job")
            return Response(
                 {'error': 'Only recruiter can create jobs'},
                 status = status.HTTP_403_FORBIDDEN
            )
        serializer = CreateJobSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"❌ Serializer validation failed: {serializer.errors}")
            return Response(
                {'error': serializer.errors},
                status= status.HTTP_400_BAD_REQUEST
            )
        logger.info("✅ Serializer validation passed")
        logger.debug(f"📋 Validated data: {serializer.validated_data}")

        company_id = request.data.get('company_id')
        if not company_id:
            return Response(
                {'error': 'Company Id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"🏢 Creating job for company: {company_id}")

        try:
            result = create_job_useCase.execute(
                recruiter_id=request.user.id,
                company_id=company_id,
                job_data=serializer.validated_data
            )
            
            logger.debug(f"📤 Use case result: {result}")
            
            # ✅ FIX: Changed 'successs' to 'success'
            if not result['success']:
                logger.error(f"❌ Job creation failed: {result.get('error')}")
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"✅ Job created successfully: {result['job'].get('id')}")
            return Response(
                {
                    'message': result['message'],
                    'job': result['job']
                },
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.exception(f"💥 Unexpected error creating job: {str(e)}")
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FetchActiveJobs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            res = fetch_active_jobs_usecase.execute()
            if not res['success']:
                logger.error(f" failed to fetch jobs: {res.get('error')}")
                return Response(
                    {'error': res.get('error', "Failed to fetch jobs")},
                    status = status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(
                {'jobs': res['jobs']},
                status= status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(f"💥 Unexpected error: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class GetJobsByRecruiter(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            res = get_recrutir_jobs_usecase.execute(request.user.id)
            if not res['success']:
                logger.error(f" failed to fetch jobs: {res.get('error')}")
                return Response(
                    {'error': res.get('error', 'Failed to fetch jobs')},
                    status= status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(
                {'jobs' : res['jobs']},
                status = status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(f"💥 Unexpected error: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )