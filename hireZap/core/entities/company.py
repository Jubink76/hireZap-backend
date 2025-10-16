from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from decimal import Decimal

@dataclass
class Company:
    id: Optional[int] = None
    recruiter_id: Optional[int] = None
    company_name: str = ""
    logo_url : Optional[str] = None
    business_certificate: Optional[str] = None
    business_email: str = ""
    phone_number: str = ""
    industry: str = ""
    company_size: str = ""
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    address: str = ""
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    verification_status: str = "pending"  # pending, verified, rejected
    founded_year: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert entity to dictionary"""
        return {
            'id': self.id,
            'recruiter_id': self.recruiter_id,
            'company_name': self.company_name,
            'logo_url': self.logo_url,
            'business_certificate': self.business_certificate,
            'business_email': self.business_email,
            'phone_number': self.phone_number,
            'industry': self.industry,
            'company_size': self.company_size,
            'website': self.website,
            'linkedin_url': self.linkedin_url,
            'address': self.address,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'verification_status': self.verification_status,
            'founded_year': self.founded_year,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_verified(self) -> bool:
        """Check if company is verified"""
        return self.verification_status == "verified"
    
    def is_pending(self) -> bool:
        """Check if company verification is pending"""
        return self.verification_status == "pending"