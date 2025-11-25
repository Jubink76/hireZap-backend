from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class ReactivateStageUsecase:
    def __init__(self,repository:SelectionStageRepositoryPort):
        self.repository = repository
    
    def execute(self, stage_id: int) -> dict:
        try:
            # Check if stage exists
            existing_stage = self.repository.get_stage_by_id(stage_id)
            if not existing_stage:
                return {
                    'success': False,
                    'error': 'Stage not found'
                }
            
            if existing_stage.is_active:
                return {
                    'success': False,
                    'error': 'Stage is already active'
                }
            
            # Reactivate the stage
            reactivated_stage = self.repository.reactivate_stage(stage_id)
            
            if not reactivated_stage:
                return {
                    'success': False,
                    'error': 'Failed to reactivate stage'
                }
            
            return {
                'success': True,
                'data': reactivated_stage.to_dict(),
                'message': f'Stage "{reactivated_stage.name}" reactivated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error reactivating stage: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to reactivate stage: {str(e)}'
            }