from typing import Dict,Any
from core.entities.candidate_profile import Certification
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort

class AddCertificationUsecase:
    def __init__(self,candidate_repository:CandidateRepositoryPort):
        self.candidate_repository = candidate_repository
    
    def execute(self,candidate_id:int,certification_data:dict) -> Dict[str,Any]:
        certification = Certification(
            candidate_id=candidate_id,
            name=certification_data.get("name"),
            issuer=certification_data.get("issuer"),
            field=certification_data.get("field"),
            issue_date=certification_data.get("issue_date"),
            expiry_date=certification_data.get("expiry_date"),
            credential_url=certification_data.get("credential_url")
        )

        created_certification = self.candidate_repository.add_certification(certification)
        
        if not created_certification:
            return {
                "success": False,
                "error": "Failed to add certification"
            }
        
        return {
            "success": True,
            "message": "Certification added successfully",
            "certification": created_certification.to_dict()
        }