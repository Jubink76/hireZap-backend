from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class GetStageByIdUsecase:
    def __init__(self,repository:SelectionStageRepositoryPort):
        self.repository = repository
    
    def execute(self,stage_id:int) -> Dict[str, Any]:
        try:
            stage = self.repository.get_stage_by_id(stage_id)
            if not stage:
                return {
                    'success': False,
                    'error': 'Stage not found'
                }
            
            return {
                'success': True,
                'data': stage.to_dict()
            }
        
        except Exception as e:
            logger.error(f"Get stage by ID error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch stage'
            }