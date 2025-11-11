from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime

@dataclass
class CandidateProfile:
    user_id: int  # This is also candidate_id
    
    # Optional fields - filled in later
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    location: Optional[str] = None
    resume_url: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'bio': self.bio,
            'phone_number': self.phone_number,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'location': self.location,
            'resume_url': self.resume_url,
            'website': self.website,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

@dataclass
class Education:
    candidate_id: int
    degree: str
    field_of_study: str
    institution: str
    start_year: int
    
    id: Optional[int] = None
    end_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'degree': self.degree,
            'field_of_study': self.field_of_study,
            'institution': self.institution,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_current(self) -> bool:
        """Check if currently studying"""
        return self.end_year is None
@dataclass
class Experience:
    candidate_id: int
    company_name: str
    role: str
    start_date: date
    
    id: Optional[int] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'company_name': self.company_name,
            'role': self.role,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_current(self) -> bool:
        """Check if currently working"""
        return self.end_date is None
    
    def duration_in_months(self) -> int:
        """Calculate experience duration in months"""
        end = self.end_date or date.today()
        years = end.year - self.start_date.year
        months = end.month - self.start_date.month
        return years * 12 + months

@dataclass 
class Skill:
    candidate_id: int
    skill_name: str
    proficiency: int  # 1-5 star rating
    
    id: Optional[int] = None
    years_of_experience: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'skill_name': self.skill_name,
            'proficiency': self.proficiency,
            'years_of_experience': self.years_of_experience,
            'proficiency_label': self.proficiency_label(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def proficiency_label(self) -> str:
        """Get text label for proficiency level"""
        labels = {
            1: "Beginner",
            2: "Elementary",
            3: "Intermediate",
            4: "Advanced",
            5: "Expert"
        }
        return labels.get(self.proficiency, "Unknown")
    
    def is_expert(self) -> bool:
        """Check if expert level"""
        return self.proficiency >= 4

@dataclass
class Certification:
    candidate_id: int
    name: str
    issuer: str
    field: str
    
    id: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'name': self.name,
            'issuer': self.issuer,
            'field': self.field,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'credential_url': self.credential_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_expired(self) -> bool:
        """Check if certification has expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()
    
    def is_valid(self) -> bool:
        """Check if certification is still valid"""
        return not self.is_expired()
    