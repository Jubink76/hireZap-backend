from typing import Dict, Any
from core.entities.candidate_profile import Experience
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort

class AddExperienceUsecase:
    def __init__(self,candidate_repository:CandidateRepositoryPort):
        self.candidate_repository = candidate_repository
    
    def execute(self,candidate_id:int, experience_data:dict) -> Dict[str,Any]:
        experience = Experience(
            candidate_id=candidate_id,
            company_name=experience_data.get("company_name"),
            role=experience_data.get("role"),
            start_date=experience_data.get("start_date"),
            end_date=experience_data.get("end_date"),
            description=experience_data.get("description")
        )
        created_experience = self.candidate_repository.add_experience(experience)
        
        if not created_experience:
            return {
                "success": False,
                "error": "Failed to add experience"
            }
        
        return {
            "success": True,
            "message": "Experience added successfully",
            "experience": created_experience.to_dict()
        }