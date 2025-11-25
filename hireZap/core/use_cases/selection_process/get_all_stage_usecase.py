from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class GetAllStageUsecase:
    def __init__(self,repository:SelectionStageRepositoryPort):
        self.repository = repository

    def execute(self) -> Dict[str, Any]:
        try:
            stages = self.repository.get_all_stages()
            if not stages:
                return {
                    'success':False,
                    'error':"Failed to fetch all stages"
                }
            return {
                'success':True,
                'data':[stage.to_dict() for stage in stages],
                'count':len(stages)
            }
        except Exception as e:
            logger.error(f"Get all stages error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch stages'
            }