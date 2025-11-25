from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class GetInactiveStages:
    def __init__(self,repository:SelectionStageRepositoryPort):
        self.repository = repository
    
    def execute(self) -> dict:
        try:
            stages = self.repository.get_inactive_stages()
            return {
                'success': True,
                'data': [stage.to_dict() for stage in stages],
                'message': 'Inactive stages retrieved successfully'
            }
        except Exception as e:
            logger.error(f"Error fetching inactive stages: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to fetch inactive stages',
                'data': []
            }
