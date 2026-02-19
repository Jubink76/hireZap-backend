from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from core.use_cases.admin.admin_usecases import(
    GetDashboardStatsUseCase,
    GetAllCandidatesUseCase,
    GetCandidateDetailsUseCase,
    SearchCandidatesUseCase,
    GetAllRecruitersUseCase,
    GetRecruiterDetailsUseCase,
    GetAllJobsWithDetailsUseCase,
    GetJobDetailsUseCase,
    GetAllApplicationsWithDetailsUseCase,
    GetApplicationDetailsUseCase
)
from infrastructure.repositories.admin_repository import AdminRepository

import logging

logger = logging.getLogger(__name__)


class BaseAdminView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_repo = AdminRepository()


# ========== DASHBOARD ==========
class AdminDashboardView(BaseAdminView):
    def get(self, request):
        usecase = GetDashboardStatsUseCase(self.admin_repo)
        result = usecase.execute()
        
        if not result['success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)


# ========== CANDIDATES ==========
class AdminCandidatesListView(BaseAdminView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        # Build filters
        filters = {}
        if request.query_params.get('is_active'):
            filters['is_active'] = request.query_params.get('is_active') == 'true'
        if request.query_params.get('location'):
            filters['location'] = request.query_params.get('location')
        
        usecase = GetAllCandidatesUseCase(self.admin_repo)
        result = usecase.execute(page, page_size, filters if filters else None)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminCandidateDetailView(BaseAdminView):
    
    def get(self, request, user_id):
        usecase = GetCandidateDetailsUseCase(self.admin_repo)
        result = usecase.execute(user_id)
        
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND 
                if 'not found' in result.get('error', '').lower() 
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminCandidateSearchView(BaseAdminView):
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        usecase = SearchCandidatesUseCase(self.admin_repo)
        result = usecase.execute(query)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


# ========== RECRUITERS ==========
class AdminRecruitersListView(BaseAdminView):
    
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        usecase = GetAllRecruitersUseCase(self.admin_repo)
        result = usecase.execute(page, page_size)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminRecruiterDetailView(BaseAdminView):
    
    def get(self, request, user_id):
        usecase = GetRecruiterDetailsUseCase(self.admin_repo)
        result = usecase.execute(user_id)
        
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND 
                if 'not found' in result.get('error', '').lower() 
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)


# ========== JOBS ==========
class AdminJobsListView(BaseAdminView):
    
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        usecase = GetAllJobsWithDetailsUseCase(self.admin_repo)
        result = usecase.execute(page, page_size)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminJobDetailView(BaseAdminView):
    
    def get(self, request, job_id):
        usecase = GetJobDetailsUseCase(self.admin_repo)
        result = usecase.execute(job_id)
        
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND 
                if 'not found' in result.get('error', '').lower() 
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)


# ========== APPLICATIONS ==========
class AdminApplicationsListView(BaseAdminView):
    
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        usecase = GetAllApplicationsWithDetailsUseCase(self.admin_repo)
        result = usecase.execute(page, page_size)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminApplicationDetailView(BaseAdminView):
    
    def get(self, request, application_id):
        usecase = GetApplicationDetailsUseCase(self.admin_repo)
        result = usecase.execute(application_id)
        
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND 
                if 'not found' in result.get('error', '').lower() 
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)