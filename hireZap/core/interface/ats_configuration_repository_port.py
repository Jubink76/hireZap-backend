from typing import Dict, Optional
from abc import ABC, abstractmethod

class ATSConfigurationRepositoryPort(ABC):
    @abstractmethod
    def upsert(self, job_id:int, config_data:Dict):
        """Create or Update ATS config"""
        pass

    @abstractmethod
    def get_by_job_id(self,job_id:int):
        """Fetch ATS config by job id"""
        pass
    