from core.entities.candidate_profile import CandidateProfile
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort
from typing import Dict, Any

class UpdateProfileUsecase:
    def __init__(self,candidate_repository:CandidateRepositoryPort):
        self.candidate_repository = candidate_repository

    def execute(self,user_id:int,profile_data:dict) -> Dict[str,Any]:
        existing_profile =self.candidate_repository.get_profile_by_user_id(user_id)
        if not existing_profile:
            return {
                'success' : False,
                'error' : "Profile not found"
            }
        updated_profile = CandidateProfile(
            user_id=user_id,
            bio=profile_data.get("bio", existing_profile.bio),
            phone_number=profile_data.get("phone_number", existing_profile.phone_number),
            linkedin_url=profile_data.get("linkedin_url", existing_profile.linkedin_url),
            github_url=profile_data.get("github_url", existing_profile.github_url),
            location=profile_data.get("location", existing_profile.location),
            resume_url=profile_data.get("resume_url", existing_profile.resume_url),
            website=profile_data.get("website", existing_profile.website)
        )
        saved_profile = self.candidate_repository.update_profile(updated_profile)
        if not saved_profile:
            return {
                'success' : False,
                'error' : "Failed to update profile"
            }
        return {
            'success': True,
            'message': "profile updated successfully",
            "profile" : saved_profile.to_dict(),
        }