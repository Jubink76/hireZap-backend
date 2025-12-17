from core.interface.job_selection_process_repository_port import JobSelectionProcessRepositoryPort
import logging 
logger = logging.getLogger(__name__)
from typing import List

class GetJobSelectionProcessUsecase:
    def __init__(self,repository:JobSelectionProcessRepositoryPort):
        self.repository = repository
    def execute(self,job_id:int) -> dict:
        try:
            stages = self.repository.get_job_selection_stages(job_id)
            if not stages:
                return {
                    'success':False,
                    'error':"Failed to fetch stages"
                }
            return {
                'success': True,
                'data': [stage.to_dict() for stage in stages],
                'message': 'Job selection stages retrieved successfully'
            }
        except Exception as e:
            logger.error(f"Error fetching job selection stages: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to fetch selection stages: {str(e)}',
                'data': []
            }