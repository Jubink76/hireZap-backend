from typing import Dict, Any
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort

class GetCompleteProfileUsecase:
    def __init__(self,candidate_repository:CandidateRepositoryPort):
        self.candidate_repository = candidate_repository
    
    def execute(self,user_id:int) -> Dict[str,Any]:
        profile = self.candidate_repository.get_profile_by_user_id(user_id)
        if not profile:
            return {
                'success': False,
                'error' : "Profile not found"
            }
        educations = self.candidate_repository.get_educations(user_id)
        experiences = self.candidate_repository.get_experiences(user_id)
        skills = self.candidate_repository.get_skills(user_id)
        certifications = self.candidate_repository.get_certifications(user_id)
        return {
            "success": True,
            "profile": profile.to_dict(),
            "educations": [edu.to_dict() for edu in educations],
            "experiences": [exp.to_dict() for exp in experiences],
            "skills": [skill.to_dict() for skill in skills],
            "certifications": [cert.to_dict() for cert in certifications],
            "stats": {
                "total_skills": len(skills),
                "expert_skills": len([s for s in skills if s.is_expert()]),
                "total_experience_months": sum(exp.duration_in_months() for exp in experiences if hasattr(exp, 'duration_in_months')),
                "current_role": next((exp.role for exp in experiences if exp.is_current()), None),
                "valid_certifications": len([c for c in certifications if c.is_valid()])
            }
        }