from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.entities.user import UserEntity
from core.entities.candidate_profile import(
    CandidateProfile,
    Skill,
    Certification,
    Education,
    Experience  
)
from core.entities.company import Company
from core.entities.job import Job
from core.entities.application import Application

@dataclass
class CandidateInfo:
    """ complete candidate information"""
    user_id : int
    email : str
    full_name: str
    role : str
    is_active : bool
    created_at : datetime
    last_login : Optional[datetime]

    # profile data
    profile_id : Optional[int]
    phone : Optional[str]
    location : Optional[str]
    bio : Optional[str]
    profile_picture : Optional[str]
    resume : Optional[str]

    # aggregated data
    educations: List[Dict[str, Any]]
    experiences: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]

    total_applications : int

    def to_dict(self) -> dict:
        return {
            'user_id':self.user_id,
            'email': self.email,
            'full_name': self.full_name,
            'role' : self.role,
            'is_active' : self.is_active,
            'created_at' : self.created_at.isoformat() if self.created_at else None,
            'last_login' : self.last_login.isoformat() if self.last_login else None,
            'profile_id' : self.profile_id,
            'phone' : self.phone,
            'location' : self.location,
            'bio' : self.bio,
            'profile_picture' : self.profile_picture,
            'resume' : self.resume,
            'eduction' : self.educations,
            'experience' : self.experiences,
            'skill' : self.skills,
            'certifications' : self.certifications,
            'total_applications' : self.total_applications
        }
    
@dataclass
class RecruiterInfo:
    """ Commplete recruiter informations """
    user_id : int
    email : str
    full_name : str
    role : str
    is_active : bool
    created_at : datetime
    last_login : Optional[datetime]

    company : Optional[Dict[str, Any]]
    # stats 
    total_jobs_posted : int
    active_jobs : int 
    total_application_recieved : int

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'email' : self.email,
            'full_name' : self.full_name,
            'role' : self.role,
            'is_active' : self.is_active,
            'created_at' : self.created_at.isoformat() if self.created_at else None,
            'last_login' : self.last_login.isoformat() if self.last_login else None,
            'company' : self.company,
            'total_jobs_posted': self.total_jobs_posted,
            'active_jobs' : self.active_jobs,
            'total_application_recieved' : self.total_application_recieved
        }
    
@dataclass
class JobInfo:
    job : Dict[str,Any]
    company : Dict[str, Any]
    recruiter_email : str
    total_applications : int
    application_by_status : Dict[str, int]

    def to_dict(self):
        return {
            'job' : self.job,
            'company' : self.company,
            'recruiter_email' : self.recruiter_email,
            'total_applications' : self.total_applications,
            'applications_by_status' : self.application_by_status
        }
    
@dataclass
class ApplicationInfo:
    application : Dict[str,Any]
    candidate_name : str
    candidate_email : str
    candidate_phone : Optional[str]
    job_title : str
    company_name : str
    recruiter_name : str
    recruiter_email : str

    def to_dict(self) -> dict:
        return {
            'application' : self.application,
            'candidate_name' : self.candidate_name,
            'candidate_email' : self.candidate_email,
            'candidate_phone' : self.candidate_phone,
            'job_title' : self.job_title,
            'company_name' : self.company_name,
            'recruiter_name' : self.recruiter_name,
            'recruiter_email' :  self.recruiter_email
        }
    
@dataclass
class AdminDashboardStats:
    total_candidates : int
    total_recruiters : int
    total_companies : int
    total_jobs : int
    total_applications : int
    pending_companies : int
    active_jobs : int 
    applications_by_status : Dict[str, Any]
    recent_candidates : int
    recent_applications : int

    def to_dict(self) -> dict:
        return {
            'total_candidates' : self.total_candidates,
            'total_recruiters' : self.total_recruiters,
            'total_companies' : self.total_companies,
            'total_jobs' : self.total_jobs,
            'total_applications' : self.total_applications,
            'pending_companies' : self.pending_companies,
            'active_jobs' : self.active_jobs,
            'applications_by_status' : self.applications_by_status,
            'recent_candidates': self.recent_candidates,
            'recent_applications' : self.recent_applications
        }