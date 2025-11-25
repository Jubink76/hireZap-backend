from typing import Dict, Any, List
from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage
import logging
import re
logger = logging.getLogger(__name__)

class CreateStageUsecase:
    def __init__(self,repository:SelectionStageRepositoryPort):
        self.repository = repository
    
    def execute(self,stage_data:dict) -> Dict[str,Any]:
        try:
            # Validation
            if not stage_data.get('name'):
                return {'success': False, 'error': 'Stage name is required'}
            
            # Generate slug from name
            from django.utils.text import slugify
            slug = slugify(stage_data['name'])
            
            # # Check if slug already exists
            # if self.repository.get_stage_by_slug(slug):
            #     return {
            #         'success': False,
            #         'error': 'Stage with this name already exists'
            #     }
            
            # Get max order
            all_stages = self.repository.get_all_stages()
            max_order = max([s.order for s in all_stages], default=0)
            
            # Create entity (ID will be auto-generated)
            stage = SelectionStage(
                id=0,  # Placeholder, will be set by database
                slug=slug,
                name=stage_data['name'],
                description=stage_data['description'],
                icon=stage_data.get('icon', 'FileText'),
                duration=stage_data.get('duration', ''),
                requires_premium=stage_data.get('requiresPremium', False),
                tier=stage_data.get('tier', 'free'),
                is_default=False,
                order=max_order + 1,
                is_active=True,
                created_at=None,
                updated_at=None
            )
            
            created_stage = self.repository.create_stage(stage)
            
            return {
                'success': True,
                'data': created_stage.to_dict(),
                'message': 'Stage created successfully'
            }
        
        except Exception as e:
            logger.error(f"Create stage error: {str(e)}")
            return {'success': False, 'error': 'Failed to create stage'}