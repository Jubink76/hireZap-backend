from typing import Dict,Any
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort
from core.entities.candidate_profile import Education

class AddEducationUsecase:
    def __init__(self,candidate_repository:CandidateRepositoryPort):
        self.candidate_repository = candidate_repository
    
    def execute(self,candidate_id:int,educational_data:dict) -> Dict[str,Any]:
        education = Education(
            candidate_id=candidate_id,
            degree=educational_data.get("degree"),
            field_of_study=educational_data.get("field_of_study"),
            institution=educational_data.get("institution"),
            start_year=educational_data.get("start_year"),
            end_year=educational_data.get("end_year")
        )

        created_education = self.candidate_repository.add_education(education)
        
        if not created_education:
            return {
                "success": False,
                "error": "Failed to add education"
            }
        
        return {
            "success": True,
            "message": "Education added successfully",
            "education": created_education.to_dict()
        }