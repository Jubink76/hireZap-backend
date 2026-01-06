from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Application:
    job_id:int
    candidate_id:int
    first_name:str
    last_name:str
    email:str

    #optional fields
    id:Optional[int] = None
    resume_url:Optional[str] = None
    portfolio_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_profile: Optional[str] = None
    years_of_experience: Optional[str] = None
    availability: Optional[str] = None
    expected_salary: Optional[str] = None
    current_company: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str = 'applied'
    is_draft: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    interview_date: Optional[datetime] = None
    recruiter_notes: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_logo: Optional[str] = None

    screening_status: str = 'pending',
    screening_decision: str = 'pending',
    screening_scores: Optional[Dict[str, int]] = None,
    screening_details: Optional[Dict[str, Any]] = None,
    screened_at: Optional[datetime] = None,
    current_stage_id: Optional[int] = None,
    current_stage_status: str = 'pending',

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'candidate_id': self.candidate_id,
            'resume_url': self.resume_url,
            'portfolio_url': self.portfolio_url,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'linkedin_profile': self.linkedin_profile,
            'years_of_experience': self.years_of_experience,
            'availability': self.availability,
            'expected_salary': self.expected_salary,
            'current_company': self.current_company,
            'cover_letter': self.cover_letter,
            'status': self.status,
            'is_draft': self.is_draft,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'rejection_reason':self.rejection_reason,
            'interview_date':self.interview_date.isoformat() if self.interview_date else None,
            'recruiter_notes':self.recruiter_notes,
            'job_title':self.job_title,
            'company_name':self.company_name,
            'company_logo':self.company_logo,
            'screening_status': self.screening_status,
            'screening_decision': self.screening_decision,
            'screening_scores': self.screening_scores,
            'screening_details': self.screening_details,
            'screened_at': self.screened_at.isoformat() if self.screened_at else None,
            'current_stage_id': self.current_stage_id,
            'current_stage_status': self.current_stage_status,
            
        }

    def is_submitted(self) -> bool:
        """Check if application is submitted (not draft)"""
        return not self.is_draft and self.submitted_at is not None

    def can_be_withdrawn(self) -> bool:
        """Check if application can be withdrawn"""
        return self.status in ['applied', 'under_review']