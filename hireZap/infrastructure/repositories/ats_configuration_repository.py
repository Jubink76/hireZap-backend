from resume_screening.models import ATSConfiguration
from core.interface.ats_configuration_repository_port import ATSConfigurationRepositoryPort

class ATSConfigRepository(ATSConfigurationRepositoryPort):

    def upsert(self,job_id:int, config_data:dict) -> ATSConfiguration:
        try:
            ats_config, _ = ATSConfiguration.objects.update_or_create(
                job_id=job_id,
                defaults=config_data
            )
            return ats_config
        except ATSConfiguration.DoesNotExist:
            return None
    
    def get_by_job_id(self,job_id:int):
        try:
            return ATSConfiguration.objects.get(job_id=job_id)
        except ATSConfiguration.DoesNotExist:
            return None