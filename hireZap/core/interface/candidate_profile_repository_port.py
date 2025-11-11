from abc import ABC, abstractmethod
from typing import Optional, List
from core.entities.candidate_profile import (
    CandidateProfile,
    Education,
    Experience,
    Skill,
    Certification
)


class CandidateRepositoryPort(ABC):
    """Repository interface for candidate profile operations"""
    
    @abstractmethod
    def get_profile_by_user_id(self, user_id: int) -> Optional[CandidateProfile]:
        """Get profile by user id"""
        raise NotImplementedError
    
    @abstractmethod
    def update_profile(self, profile: CandidateProfile) -> Optional[CandidateProfile]:
        """Update the profile section"""
        raise NotImplementedError
    
    # Educational methods
    @abstractmethod
    def get_educations(self, candidate_id: int) -> List[Education]:
        """Get all educational records of the particular candidate"""
        raise NotImplementedError
    
    @abstractmethod
    def add_education(self, education: Education) -> Education:
        """Add educational details"""
        raise NotImplementedError
    
    @abstractmethod
    def get_education_by_id(self, education_id: int) -> Optional[Education]:
        """Get education by id"""
        raise NotImplementedError
    
    @abstractmethod
    def update_education(self, education: Education) -> Education:
        """Update existing education record"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_education(self, education_id: int) -> bool:
        """Delete educational record"""
        raise NotImplementedError
    
    # Experience methods
    @abstractmethod
    def get_experiences(self, candidate_id: int) -> List[Experience]:
        """Get all the experiences of particular user"""
        raise NotImplementedError
    
    @abstractmethod
    def add_experience(self, experience: Experience) -> Experience:
        """Add experience details"""
        raise NotImplementedError
    
    @abstractmethod
    def get_experience_by_id(self, experience_id: int) -> Optional[Experience]:
        """Get particular experience"""
        raise NotImplementedError
    
    @abstractmethod
    def update_experience(self, experience: Experience) -> Experience:
        """Update particular experience"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_experience(self, experience_id: int) -> bool:
        """Delete particular experience"""
        raise NotImplementedError
    
    # Skill methods
    @abstractmethod
    def get_skills(self, candidate_id: int) -> List[Skill]:
        """Get all the skills"""
        raise NotImplementedError
    
    @abstractmethod
    def add_skill(self, skill: Skill) -> Skill:
        """Add a new skill"""
        raise NotImplementedError
    
    @abstractmethod
    def get_skill_by_id(self, skill_id: int) -> Optional[Skill]:
        """Get skill by id"""
        raise NotImplementedError

    @abstractmethod
    def update_skill(self, skill: Skill) -> Skill:
        """Update particular skill"""
        raise NotImplementedError

    @abstractmethod
    def delete_skill(self, skill_id: int) -> bool:
        """Delete skill by id"""
        raise NotImplementedError

    # Certification methods
    @abstractmethod
    def get_certifications(self, candidate_id: int) -> List[Certification]:
        """List all the certificates"""
        raise NotImplementedError
    
    @abstractmethod
    def add_certification(self, certification: Certification) -> Certification:
        """Add certificate"""
        raise NotImplementedError
    
    @abstractmethod
    def get_certification_by_id(self, certification_id: int) -> Optional[Certification]:
        """Get particular certification by id"""
        raise NotImplementedError
    
    @abstractmethod
    def update_certification(self, certification: Certification) -> Certification:
        """Update particular certificate"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_certification(self, certification_id: int) -> bool:
        """Delete particular certificate"""
        raise NotImplementedError
    
    # Complete profile
    @abstractmethod
    def get_complete_profile(self, user_id: int) -> Optional[dict]:
        """Get complete profile with all related data (profile-bio, education, experience, skills, certifications)"""
        raise NotImplementedError