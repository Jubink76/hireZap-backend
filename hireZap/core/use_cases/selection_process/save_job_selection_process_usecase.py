from core.interface.job_selection_process_repository_port import JobSelectionProcessRepositoryPort
import logging 
logger = logging.getLogger(__name__)
from typing import List

class SaveJobSelectionProcessUsecase:
    def __init__(self,repository:JobSelectionProcessRepositoryPort):
        self.repository = repository

    def execute(self,job_id:int, stage_ids:List[int]) -> dict:
        try:
            if not stage_ids:
                return{
                    'success':False,
                    'error':"Atleast one stage must be selected"
                }
            processes = self.repository.save_job_selection_process(job_id,stage_ids)
            if not processes:
                return{
                    'success':False,
                    'error':"Cannot process the stages"
                }
            return {
                'success': True,
                'data': {
                    'job_id': job_id,
                    'stages_count': len(processes)
                },
                'message': 'Selection process saved successfully'
            }
        except Exception as e:
            logger.error(f"Error saving job selection process: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to save selection process: {str(e)}'
            }