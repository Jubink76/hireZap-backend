from typing import List, Optional, Dict, Any, Tuple
from django.db.models import Prefetch, Count, Q, F
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from core.interface.admin_repository_port import AdminRepositoryPort
from core.entities.admin_entity import *
from accounts.models import User
from candidate.models import (
    CandidateProfile,
    CandidateEducation,
    CandidateSkill,
    CandidateExperience,
    CandidateCertification
)
from companies.models import Company
from application.models import ApplicationModel
from job.models import JobModel

import logging 
logger = logging.getLogger(__name__)

class AdminRepository(AdminRepositoryPort):

    def get_dashboard_stats(self):
        cache_key = 'admin:dashboard:stats:v1'
        stats = cache.get(cache_key)

        if stats is None:
            logger.info("Cache miss for dashboard stats - computing from database")
            stats = self._compute_dashboard_stats()
            cache.set(cache_key, stats, 300) # cache for 5 minutes
        else:
            logger.info("Cache hit for dashboard stats")
        return stats
    
    def compute_dashboard_stats(self) -> AdminDashboardStats:

        total_candidates = User.objects.filter(role = 'candidate').count()
        total_recruiters = User.objects.filter(role = 'recruiter').count()
        total_companies = Company.objects.count()
        total_jobs = JobModel.objects.count()
        total_applications = ApplicationModel.objects.count()

        pending_companies = Company.objects.filter(verification_status ='pending').count()
        active_jobs = Job.objects.filter(status='active').count()

        applications_by_status = dict(
            ApplicationModel.objects.values('status').annotate(
                count=Count('id')
            ).values_list('status','count')
        )

        # recent metrics ( last 7 days )
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_candidates = User.objects.filter(
            role='candidate',
            created_at__gte=seven_days_ago
        ).count()

        recent_applications = ApplicationModel.objects.filter(
            applied_at__gte = seven_days_ago
        ).count()

        return AdminDashboardStats(
            total_candidates=total_candidates,
            total_recruiters=total_recruiters,
            total_companies=total_companies,
            total_jobs=total_jobs,
            total_applications=total_applications,
            pending_companies=pending_companies,
            active_jobs=active_jobs,
            applications_by_status=applications_by_status,
            recent_candidates=recent_candidates,
            recent_applications=recent_applications
        )
    
    ## Candidate ##

    def get_all_candidate(
            self,
            page:int = 1, 
            page_size:int = 10, 
            filters: Optional[Dict[str,Any]] = None
            ) -> tuple[List[CandidateInfo], int]:
        
        queryset = User.objects.filter(role='candidate')

        if filters:
            if filters.get('is_active') is not None:
                queryset = queryset.filter(is_active=filters['is_active'])
            if filters.get('location'):
                queryset = queryset.filter(
                    CandidateProfile__location__icontains = filters['lcoation']
                )

        queryset =  queryset.select_related(
            'candidateprofile'
        ).prefetch_related(
            'candidateprofile__educations',
            'candidateprofile__experiences',
            'candidateprofile__skills',
            'candidateprofile__certifications',
            'candidateprofile__applications'
        ).annotate(
            application_count=Count('candidateprofile__applications')
        ).order_by('-created_at')
        
        count_cache_key = f'admin:candidates:count:{hash(str(filters))}'
        total_count = cache.get(count_cache_key)

        if total_count is None:
            total_count = queryset.count()
            cache.set(count_cache_key, total_count, 600)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = queryset[start:end]
        
        # Convert to entities
        candidates = []
        for user in paginated_users:
            candidate_info = self._user_to_candidate_info(user)
            candidates.append(candidate_info)
        
        return candidates, total_count
    
    def candidate_by_id(self,user_id:int) -> Optional[CandidateInfo]:
        try:
            user = User.objects.filter(
                id=user_id,
                role='candidate'
            ).select_related(
                'candidateprofile'
            ).prefetch_related(
                'candidateprofile__educations',
                'candidateprofile__experiences',
                'candidateprofile__skills',
                'candidateprofile__certifications',
                'candidateprofile__applications'
            ).annotate(
                application_count=Count('candidateprofile__applications')
            ).first()

            if not user:
                return None
            
            return self._user_to_candidate_info(user)
        
        except User.DoesNotExist:
            return None
        
    def search_candidate(self, query: str) -> List[CandidateInfo]:
        """Search candidates by name, email, location"""
        users = User.objects.filter(
            role='candidate'
        ).filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(candidateprofile__location__icontains=query)
        ).select_related(
            'candidateprofile'
        ).prefetch_related(
            'candidateprofile__educations',
            'candidateprofile__experiences',
            'candidateprofile__skills',
            'candidateprofile__certifications'
        ).annotate(
            application_count=Count('candidateprofile__applications')
        )[:50]  # Limit search results
        
        return [self._user_to_candidate_info(user) for user in users]
    

    ## recruiter ##
    def get_all_recruiters(
        self, 
        page: int = 1, 
        page_size: int = 10
    ) -> tuple[List[RecruiterInfo], int]:
        """Get all recruiters with company and job stats"""
        
        queryset = User.objects.filter(
            role='recruiter'
        ).prefetch_related(
            'company',
            'posted_jobs'
        ).annotate(
            jobs_count=Count('posted_jobs'),
            active_jobs_count=Count('posted_jobs', filter=Q(posted_jobs__status='active'))
        ).order_by('-created_at')
        
        total_count = queryset.count()
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = queryset[start:end]
        
        recruiters = []
        for user in paginated_users:
            recruiter_info = self._user_to_recruiter_info(user)
            recruiters.append(recruiter_info)
        
        return recruiters, total_count
    
    def get_recruiter_by_id(self, user_id: int) -> Optional[RecruiterInfo]:
        """Get single recruiter with details"""
        try:
            user = User.objects.filter(
                id=user_id,
                role='recruiter'
            ).prefetch_related(
                'company',
                'posted_jobs'
            ).annotate(
                jobs_count=Count('posted_jobs'),
                active_jobs_count=Count('posted_jobs', filter=Q(posted_jobs__status='active'))
            ).first()
            
            if not user:
                return None
            
            return self._user_to_recruiter_info(user)
        
        except User.DoesNotExist:
            return None

    ## jobs ##    
    
    def get_all_jobs_with_detail(
        self, 
        page: int = 1, 
        page_size: int = 10
    ) -> tuple[List[JobInfo], int]:
        """Get all jobs with company and application stats"""
        
        queryset = JobModel.objects.select_related(
            'company',
            'recruiter'
        ).prefetch_related(
            'applications'
        ).annotate(
            applications_count=Count('applications')
        ).order_by('-created_at')
        
        total_count = queryset.count()
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated_jobs = queryset[start:end]
        
        jobs = []
        for job in paginated_jobs:
            job_info = self._job_to_job_info(job)
            jobs.append(job_info)
        
        return jobs, total_count
    
    def get_job_details(self, job_id: int) -> Optional[JobInfo]:
        """Get single job with all details"""
        try:
            job = JobModel.objects.select_related(
                'company',
                'recruiter'
            ).prefetch_related(
                'applications'
            ).annotate(
                applications_count=Count('applications')
            ).get(id=job_id)
            
            return self._job_to_job_info(job)
        
        except JobModel.DoesNotExist:
            return None
        
## applications ##
    def get_all_application_with_detail(
            self, 
            page: int = 1, 
            page_size: int = 10
        ) -> tuple[List[ApplicationInfo], int]:
            """Get all applications with candidate and job details"""
            
            queryset = ApplicationModel.objects.select_related(
                'candidate__user',
                'job__company',
                'job__recruiter'
            ).order_by('-applied_at')
            
            total_count = queryset.count()
            
            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            paginated_applications = queryset[start:end]
            
            applications = []
            for application in paginated_applications:
                app_info = self._application_to_application_info(application)
                applications.append(app_info)
            
            return applications, total_count
    
    def get_application_details(self, application_id: int) -> Optional[ApplicationInfo]:
        """Get single application with all details"""
        try:
            application = ApplicationModel.objects.select_related(
                'candidate__user',
                'job__company',
                'job__recruiter'
            ).get(id=application_id)
            
            return self._application_to_application_info(application)
        
        except ApplicationModel.DoesNotExist:
            return None
        
    def _user_to_candidate_info(self, user: User) -> CandidateInfo:
        profile = getattr(user, 'candidateprofile', None)

        # Prepare lists
        educations = []
        experiences = []
        skills = []
        certifications = []

        if profile:
            educations = [
                {
                    "id": e.id,
                    "degree": e.degree,
                    "field_of_study": e.field_of_study,
                    "institution": e.institution,
                    "start_year": e.start_year,
                    "end_year": e.end_year,
                }
                for e in profile.educations.all()
            ]

            experiences = [
                {
                    "id": exp.id,
                    "company_name": exp.company_name,
                    "role": exp.role,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "description": exp.description,
                }
                for exp in profile.experiences.all()
            ]

            skills = [
                {
                    "id": s.id,
                    "skill_name": s.skill_name,
                    "proficiency": s.proficiency,
                    "years_of_experience": s.years_of_experience
                }
                for s in profile.skills.all()
            ]

            certifications = [
                {
                    "id": c.id,
                    "name": c.name,
                    "issuer": c.issuer,
                    "field": c.field,
                    "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                    "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                    "credential_url": c.credential_url
                }
                for c in profile.certifications.all()
            ]

        # Correct full name
        full_name = f"{user.full_name}".strip() or user.email.split('@')[0]

        return CandidateInfo(
            user_id=user.id,
            email=user.email,
            full_name=full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,

            # CandidateProfile fields
            profile_id=profile.user_id if profile else None,
            phone=profile.phone_number if profile else None,
            location=profile.location if profile else None,
            bio=profile.bio if profile else None,
            profile_picture=None,  # You do NOT have this field in your model now
            resume=profile.resume_url if profile else None,

            educations=educations,
            experiences=experiences,
            skills=skills,
            certifications=certifications,

            total_applications=getattr(profile, "application_count", 0)
        )


    def _user_to_recruiter_info(self, user: User) -> RecruiterInfo:
        """Convert User model to RecruiterInfo entity"""
        company = getattr(user, 'company', None)

        # Get job counts
        total_jobs = getattr(user, 'jobs_count', 0)
        active_jobs = getattr(user, 'active_jobs_count', 0)
        
        # Calculate total applications received
        total_applications = 0
        for job in user.posted_jobs.all():
            total_applications += job.applications.count()
        
        # Convert company to dict
        company_dict = None
        if company:
            company_dict = {
                'id': company.id,
                'name': company.company_name,
                'description': company.description,
                'website': company.website,
                'verification_status': company.verification_status,
                'created_at': company.created_at.isoformat() if company.created_at else None
            }
        
        # Build full name
        full_name = f"{user.full_name}".strip() or user.email.split('@')[0]
        
        return RecruiterInfo(
            user_id=user.id,
            email=user.email,
            full_name=full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            company=company_dict,
            total_jobs_posted=total_jobs,
            active_jobs=active_jobs,
            total_application_recieved=total_applications
        )
    
    def _job_to_job_info(self, job: Job) -> JobInfo:
        """Convert Job model to JobInfo entity"""
        # Convert job to dict
        job_dict = {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'requirements': job.requirements,
            'location': job.location,
            'job_type': job.job_type,
            'experience_level': job.experience_level,
            'salary_min': float(job.salary_min) if job.salary_min else None,
            'salary_max': float(job.salary_max) if job.salary_max else None,
            'status': job.status,
            'created_at': job.created_at.isoformat() if job.created_at else None
        }
        
        # Convert company to dict
        company_dict = {
            'id': job.company.id,
            'name': job.company.name,
            'location': job.company.location,
            'verification_status': job.company.verification_status
        }
        
        # Get application breakdown by status
        applications_by_status = {}
        if hasattr(job, 'applications'):
            for app in job.applications.all():
                status = app.status
                applications_by_status[status] = applications_by_status.get(status, 0) + 1
        
        total_applications = getattr(job, 'applications_count', 0)
        
        return JobInfo(
            job=job_dict,
            company=company_dict,
            recruiter_email=job.recruiter.email,
            total_applications=total_applications,
            application_by_status=applications_by_status
        )
    
    def _application_to_application_info(self, application: Application) -> ApplicationInfo:
        """Convert Application model to ApplicationInfo entity"""
        candidate_user = application.candidate.user
        candidate_name = f"{candidate_user.first_name} {candidate_user.last_name}".strip() or candidate_user.email.split('@')[0]
        
        recruiter_user = application.job.recruiter
        recruiter_name = f"{recruiter_user.first_name} {recruiter_user.last_name}".strip() or recruiter_user.email.split('@')[0]
        
        # Convert application to dict
        application_dict = {
            'id': application.id,
            'status': application.status,
            'cover_letter': application.cover_letter,
            'applied_at': application.applied_at.isoformat() if application.applied_at else None,
            'updated_at': application.updated_at.isoformat() if application.updated_at else None,
            # Add other fields if your Application model has them
        }
        
        return ApplicationInfo(
            application=application_dict,
            candidate_name=candidate_name,
            candidate_email=candidate_user.email,
            candidate_phone=application.candidate.phone if application.candidate else None,
            job_title=application.job.title,
            company_name=application.job.company.name,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_user.email
        )
    
    # Cache invalidation methods
    def invalidate_dashboard_cache(self):
        """Invalidate dashboard cache"""
        cache.delete('admin:dashboard:stats:v1')
    
    def invalidate_candidates_cache(self):
        """Invalidate candidates cache"""
        cache.delete_pattern('admin:candidates:count:*')
    
    def invalidate_all_admin_caches(self):
        """Invalidate all admin caches"""
        cache.delete_pattern('admin:*')