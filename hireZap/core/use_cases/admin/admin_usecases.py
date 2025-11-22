from typing import Dict, Any
from core.interface.admin_repository_port import AdminRepositoryPort
import logging

logger = logging.getLogger(__name__)


# ========== DASHBOARD ==========
class GetDashboardStatsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = self.admin_repo.get_dashboard_stats()
            
            return {
                'success': True,
                'data': stats.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Dashboard stats error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch dashboard statistics'
            }


# ========== CANDIDATES ==========
class GetAllCandidatesUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(
        self, 
        page: int = 1, 
        page_size: int = 10,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get all candidates with pagination"""
        try:
            # Validation
            if page < 1:
                return {
                    'success': False,
                    'error': 'Page must be greater than 0'
                }
            
            if page_size < 1 or page_size > 100:
                return {
                    'success': False,
                    'error': 'Page size must be between 1 and 100'
                }
            
            # Get candidates
            candidates, total_count = self.admin_repo.get_all_candidate(
                page, page_size, filters
            )
            
            # Convert to dicts
            return {
                'success': True,
                'data': [candidate.to_dict() for candidate in candidates],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        
        except Exception as e:
            logger.error(f"Get candidates error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch candidates'
            }


class GetCandidateDetailsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, user_id: int) -> Dict[str, Any]:
        """Get complete candidate details"""
        try:
            if user_id < 1:
                return {
                    'success': False,
                    'error': 'Invalid user ID'
                }
            
            candidate = self.admin_repo.candidate_by_id(user_id)
            
            if not candidate:
                return {
                    'success': False,
                    'error': 'Candidate not found'
                }
            
            return {
                'success': True,
                'data': candidate.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Get candidate details error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch candidate details'
            }


class SearchCandidatesUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, query: str) -> Dict[str, Any]:
        """Search candidates"""
        try:
            if not query or len(query.strip()) < 2:
                return {
                    'success': False,
                    'error': 'Search query must be at least 2 characters'
                }
            
            candidates = self.admin_repo.search_candidate(query.strip())
            
            return {
                'success': True,
                'data': [candidate.to_dict() for candidate in candidates],
                'count': len(candidates)
            }
        
        except Exception as e:
            logger.error(f"Search candidates error: {str(e)}")
            return {
                'success': False,
                'error': 'Search failed'
            }


# ========== RECRUITERS ==========
class GetAllRecruitersUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get all recruiters with pagination"""
        try:
            if page < 1 or page_size < 1 or page_size > 100:
                return {
                    'success': False,
                    'error': 'Invalid pagination parameters'
                }
            
            recruiters, total_count = self.admin_repo.get_all_recruiters(page, page_size)
            
            return {
                'success': True,
                'data': [recruiter.to_dict() for recruiter in recruiters],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        
        except Exception as e:
            logger.error(f"Get recruiters error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch recruiters'
            }


class GetRecruiterDetailsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, user_id: int) -> Dict[str, Any]:
        """Get complete recruiter details"""
        try:
            if user_id < 1:
                return {
                    'success': False,
                    'error': 'Invalid user ID'
                }
            
            recruiter = self.admin_repo.get_recruiter_by_id(user_id)
            
            if not recruiter:
                return {
                    'success': False,
                    'error': 'Recruiter not found'
                }
            
            return {
                'success': True,
                'data': recruiter.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Get recruiter details error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch recruiter details'
            }


# ========== JOBS ==========
class GetAllJobsWithDetailsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get all jobs with details"""
        try:
            if page < 1 or page_size < 1 or page_size > 100:
                return {
                    'success': False,
                    'error': 'Invalid pagination parameters'
                }
            
            jobs, total_count = self.admin_repo.get_all_jobs_with_detail(page, page_size)
            
            return {
                'success': True,
                'data': [job.to_dict() for job in jobs],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        
        except Exception as e:
            logger.error(f"Get jobs error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch jobs'
            }


class GetJobDetailsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, job_id: int) -> Dict[str, Any]:
        """Get complete job details"""
        try:
            if job_id < 1:
                return {
                    'success': False,
                    'error': 'Invalid job ID'
                }
            
            job = self.admin_repo.get_job_details(job_id)
            
            if not job:
                return {
                    'success': False,
                    'error': 'Job not found'
                }
            
            return {
                'success': True,
                'data': job.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Get job details error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch job details'
            }


# ========== APPLICATIONS ==========
class GetAllApplicationsWithDetailsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get all applications with details"""
        try:
            if page < 1 or page_size < 1 or page_size > 100:
                return {
                    'success': False,
                    'error': 'Invalid pagination parameters'
                }
            
            applications, total_count = self.admin_repo.get_all_application_with_detail(
                page, page_size
            )
            
            return {
                'success': True,
                'data': [app.to_dict() for app in applications],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        
        except Exception as e:
            logger.error(f"Get applications error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch applications'
            }


class GetApplicationDetailsUseCase:
    def __init__(self, admin_repo: AdminRepositoryPort):
        self.admin_repo = admin_repo
    
    def execute(self, application_id: int) -> Dict[str, Any]:
        """Get complete application details"""
        try:
            if application_id < 1:
                return {
                    'success': False,
                    'error': 'Invalid application ID'
                }
            
            application = self.admin_repo.get_application_details(application_id)
            
            if not application:
                return {
                    'success': False,
                    'error': 'Application not found'
                }
            
            return {
                'success': True,
                'data': application.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Get application details error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch application details'
            }