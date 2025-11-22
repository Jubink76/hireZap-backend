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
    """Base view with common admin setup"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_repo = AdminRepository()


# ========== DASHBOARD ==========
class AdminDashboardView(BaseAdminView):
    """Get admin dashboard statistics"""
    
    def get(self, request):
        """
        GET /api/admin/dashboard/
        
        Returns dashboard statistics including:
        - Total counts of candidates, recruiters, companies, jobs, applications
        - Pending companies count
        - Active jobs count
        - Applications by status
        - Recent activity (last 7 days)
        """
        usecase = GetDashboardStatsUseCase(self.admin_repo)
        result = usecase.execute()
        
        if not result['success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)


# ========== CANDIDATES ==========
class AdminCandidatesListView(BaseAdminView):
    """Get all candidates with pagination and filters"""
    permission_classes = [IsAdminUser]
    def get(self, request):
        """
        GET /api/admin/candidates/?page=1&page_size=10&is_active=true&location=New York
        
        Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 10, max: 100)
        - is_active: Filter by active status (optional)
        - location: Filter by location (optional)
        
        Returns paginated list of candidates with complete profiles
        """
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
    """Get complete candidate details"""
    
    def get(self, request, user_id):
        """
        GET /api/admin/candidates/{user_id}/
        
        Returns complete candidate information including:
        - User details
        - Profile information
        - Educations
        - Experiences
        - Skills
        - Certifications
        - Total applications count
        """
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
    """Search candidates"""
    
    def get(self, request):
        """
        GET /api/admin/candidates/search/?q=john
        
        Query Parameters:
        - q: Search query (min 2 characters)
        
        Searches in:
        - Email
        - First name
        - Last name
        - Location
        
        Returns up to 50 matching candidates
        """
        query = request.query_params.get('q', '').strip()
        
        usecase = SearchCandidatesUseCase(self.admin_repo)
        result = usecase.execute(query)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


# ========== RECRUITERS ==========
class AdminRecruitersListView(BaseAdminView):
    """Get all recruiters with pagination"""
    
    def get(self, request):
        """
        GET /api/admin/recruiters/?page=1&page_size=10
        
        Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 10, max: 100)
        
        Returns paginated list of recruiters with:
        - User details
        - Company information
        - Job statistics
        - Application statistics
        """
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        usecase = GetAllRecruitersUseCase(self.admin_repo)
        result = usecase.execute(page, page_size)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminRecruiterDetailView(BaseAdminView):
    """Get complete recruiter details"""
    
    def get(self, request, user_id):
        """
        GET /api/admin/recruiters/{user_id}/
        
        Returns complete recruiter information including:
        - User details
        - Company details
        - Total jobs posted
        - Active jobs count
        - Total applications received
        """
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
    """Get all jobs with details"""
    
    def get(self, request):
        """
        GET /api/admin/jobs/?page=1&page_size=10
        
        Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 10, max: 100)
        
        Returns paginated list of jobs with:
        - Job details
        - Company information
        - Recruiter email
        - Application statistics
        - Applications by status
        """
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        usecase = GetAllJobsWithDetailsUseCase(self.admin_repo)
        result = usecase.execute(page, page_size)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminJobDetailView(BaseAdminView):
    """Get complete job details"""
    
    def get(self, request, job_id):
        """
        GET /api/admin/jobs/{job_id}/
        
        Returns complete job information including:
        - Job details
        - Company details
        - Recruiter email
        - Total applications
        - Applications breakdown by status
        """
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
    """Get all applications with details"""
    
    def get(self, request):
        """
        GET /api/admin/applications/?page=1&page_size=10
        
        Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 10, max: 100)
        
        Returns paginated list of applications with:
        - Application details
        - Candidate information
        - Job title
        - Company name
        - Recruiter information
        """
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        usecase = GetAllApplicationsWithDetailsUseCase(self.admin_repo)
        result = usecase.execute(page, page_size)
        
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)


class AdminApplicationDetailView(BaseAdminView):
    """Get complete application details"""
    
    def get(self, request, application_id):
        """
        GET /api/admin/applications/{application_id}/
        
        Returns complete application information including:
        - Application details
        - Candidate name, email, phone
        - Job title
        - Company name
        - Recruiter name and email
        """
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