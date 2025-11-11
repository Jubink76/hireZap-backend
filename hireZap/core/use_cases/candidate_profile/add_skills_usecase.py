from typing import Dict, Any
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort
from core.entities.candidate_profile import Skill


class AddSkillUsecase:
    def __init__(self, candidate_repository: CandidateRepositoryPort):
        self.candidate_repository = candidate_repository
    
    def execute(self, candidate_id: int, skill_data: dict) -> Dict[str, Any]:
        """
        Add a new skill for a candidate with duplicate checking
        """
        # Get existing skills
        existing_skills = self.candidate_repository.get_skills(candidate_id)
        
        # Normalize skill name for comparison
        skill_name = skill_data.get('skill_name', '').strip()
        
        # Check for duplicates (case-insensitive)
        for skill in existing_skills:
            if skill.skill_name.lower() == skill_name.lower():
                return {
                    'success': False,
                    'error': f"Skill '{skill_name}' already exists"
                }
        
        # Create skill entity
        skill = Skill(
            candidate_id=candidate_id,
            skill_name=skill_name,
            proficiency=skill_data.get("proficiency"),
            years_of_experience=skill_data.get("years_of_experience", 0)
        )
        
        # Add skill through repository
        created_skill = self.candidate_repository.add_skill(skill)
        
        if not created_skill:
            return {
                "success": False,
                "error": "Failed to add skill"
            }
        
        return {
            "success": True,
            "message": "Skill added successfully",
            "skill": created_skill.to_dict()
        }