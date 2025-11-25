from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class DeleteStageUsecase:
    def __init__(self,repository: SelectionStageRepositoryPort):
        self.repository = repository
    
    def execute(self,stage_id:int) -> Dict[str, Any]:
        try:
            stage = self.repository.get_stage_by_id(stage_id)
            if not stage:
                return {
                    'success':False,
                    'error':"stage not found"
                }
            # Check if stage is default
            if stage.is_default:
                return {
                    'success': False,
                    'error': 'Cannot delete default stages'
                }
            
            deleted = self.repository.delete_stage(stage_id)
            if not deleted:
                return {
                    'success':False,
                    'error': "Failed to delete stage"
                }
            return {
                'success': True,
                'message': 'Stage deleted successfully'
            }
        
        except Exception as e:
            logger.error(f"Delete stage error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to delete stage'
            }