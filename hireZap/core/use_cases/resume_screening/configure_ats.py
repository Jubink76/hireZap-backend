from typing import Dict
from core.interface.job_repository_port import JobRepositoryPort
from core.interface.ats_configuration_repository_port import ATSConfigurationRepositoryPort

class ConfigureATSUsecase:
    def __init__(self,job_repository: JobRepositoryPort, ats_repository:ATSConfigurationRepositoryPort):
        self.job_repo = job_repository
        self.ats_repo = ats_repository

    def execute(self,job_id:int, config_data:Dict) -> Dict:
        """Configure or update ats settings for a job"""
        try:
            job = self.job_repo.get_job_by_id(job_id)
            if not job:
                return {
                    'success':False,
                    'error':'Job not found'
                }
            ats_config = self.ats_repo.upsert(job_id,config_data)

            return {
                'success':True,
                'message':'ATS configured successfully',
                'config':{
                    'id': ats_config.id,
                    'passing_score':ats_config.passing_score,
                    'skills_weight':ats_config.skills_weight,
                    'experience_weight':ats_config.experience_weight,
                    'education_weight':ats_config.education_weight,
                    'keywords_weight':ats_config.keywords_weight

                }
            }
        except Exception as e:
            return{
                'success':False,
                'error': f"ATS configuration failed, {str(e)}"
            }
        
class GetATSConfigUsecase:
    def __init__(self,ats_repository:ATSConfigurationRepositoryPort):
        self.ats_repo = ats_repository

    def execute(self,job_id: int) -> Dict:
        """Get ATS configuration for a job"""
        ats_config = self.ats_repo.get_by_job_id(job_id)

        if not ats_config:
            return {
                'success': True,
                'is_default': True,
                'config': {
                    'skills_weight': 40,
                    'experience_weight': 30,
                    'education_weight': 20,
                    'keywords_weight': 10,
                    'passing_score': 60,
                    'required_skills': [],
                    'preferred_skills': [],
                    'minimum_experience_years': 0,
                }
            }

        return {
            'success': True,
            'config': {
                'skills_weight': ats_config.skills_weight,
                'experience_weight': ats_config.experience_weight,
                'education_weight': ats_config.education_weight,
                'keywords_weight': ats_config.keywords_weight,
                'passing_score': ats_config.passing_score,
                'required_skills': ats_config.required_skills,
                'preferred_skills': ats_config.preferred_skills,
                'minimum_experience_years': ats_config.minimum_experience_years,
            }
        }