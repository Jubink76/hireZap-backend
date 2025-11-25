from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class UpdateStageUsecase:
    def __init__(self, repository:SelectionStageRepositoryPort):
        self.repository = repository
    def execute(self,stage_id:int, stage_data:dict) -> Dict[str, Any]:
        try:
            existing_stage = self.repository.get_stage_by_id(stage_id)
            if not existing_stage:
                return {
                    'success': False,
                    'error': 'Stage not found'
                }
            
            if existing_stage.is_default:
                return {
                    'success': False,
                    'error': 'Cannot modify default stages'
                }
            
            # Validation
            if 'name' in stage_data and not stage_data['name']:
                return {
                    'success': False,
                    'error': 'Stage name cannot be empty'
                }
            
            # Convert camelCase to snake_case
            update_data = {}
            field_mapping = {
                'requiresPremium': 'requires_premium',
                'isDefault': 'is_default',
                'isActive': 'is_active'
            }
            
            for key, value in stage_data.items():
                db_key = field_mapping.get(key, key)
                update_data[db_key] = value

            updated_stage = self.repository.update_stage(stage_id, update_data)

            if not updated_stage:
                return {
                    'success': False,
                    'error': 'Failed to update stage'
                }
            
            return {
                'success': True,
                'data': updated_stage.to_dict(),
                'message': 'Stage updated successfully'
            }
        
        except Exception as e:
            logger.error(f"Update stage error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update stage'
            }
            
