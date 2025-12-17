from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Job:
    # Required fields
    company_id : int
    recruiter_id : int
    job_title : str
    location : str
    work_type : str # hybrid , remote, onsite
    employment_type : str # full-time, part-time, contract, internship

    id : Optional[int] = None
    compensation_range: Optional[str] = None
    posting_date : Optional[datetime] = None
    cover_image : Optional[str] = None
    role_summary : Optional[str] = None
    skills_required : Optional[str] = None # stored as json string
    key_responsibilities : Optional[str] = None
    requirements : Optional[str] = None
    benefits : Optional[str] = None
    application_link : Optional[str] = None
    application_deadline: Optional[datetime] = None
    applicants_visibility : Optional[str] = None #public, private
    status: str="active" # active, paused, closed, draft
    created_at : Optional[datetime] = None
    updated_at : Optional[datetime] = None
    has_configured_stages: bool = False
    configured_stages_count: int = 0

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'recruiter_id': self.recruiter_id,
            'job_title': self.job_title,
            'location': self.location,
            'work_type': self.work_type,
            'employment_type': self.employment_type,
            'compensation_range': self.compensation_range,
            'posting_date': self.posting_date.isoformat() if self.posting_date else None,
            'cover_image': self.cover_image,
            'role_summary': self.role_summary,
            'skills_required': self.skills_required,
            'key_responsibilities': self.key_responsibilities,
            'requirements': self.requirements,
            'benefits': self.benefits,
            'application_link': self.application_link,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'applicants_visibility': self.applicants_visibility,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_configured_stages': self.has_configured_stages,
            'configured_stages_count': self.configured_stages_count,

        }
    
    def is_active(self) -> bool:
        """ Check if job is active """
        return self.status == 'active'
    
    def is_draft(self) -> bool:
        """ Check if job is draft """
        return self.status == "draft"
    
    


