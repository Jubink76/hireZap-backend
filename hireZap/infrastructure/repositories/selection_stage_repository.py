from core.interface.selection_stage_repository_port import SelectionStageRepositoryPort
from core.entities.selection_stage import SelectionStage as SelectionStageEntity
from selection_process.models import SelectionStageModel
from typing import Optional, List

class SelectionStageRepository(SelectionStageRepositoryPort):

    def create_stage(self,stage:SelectionStageEntity) -> SelectionStageEntity:
        from django.utils.text import slugify
        slug = stage.slug if hasattr(stage, 'slug') and stage.slug else slugify(stage.name)
        stage_model = SelectionStageModel.objects.create(
            slug = slug,
            name = stage.name,
            description=stage.description,
            icon=stage.icon,
            duration=stage.duration,
            requires_premium=stage.requires_premium,
            tier=stage.tier,
            is_default=stage.is_default,
            order=stage.order,
            is_active=stage.is_active
        )
        return self._model_to_entity(stage_model)
    
    def get_all_stages(self) -> List[SelectionStageEntity]:
        """Get all selection stages"""
        stages = SelectionStageModel.objects.filter(is_active=True).order_by('order', 'created_at')
        return [self._model_to_entity(stage) for stage in stages]
    

    def get_stage_by_id(self, stage_id: str) -> Optional[SelectionStageEntity]:
        """Get stage by ID"""
        try:
            stage_model = SelectionStageModel.objects.get(id=stage_id)
            return self._model_to_entity(stage_model)
        except SelectionStageModel.DoesNotExist:
            return None
    
    def update_stage(self, stage_id: str, stage_data: dict) -> Optional[SelectionStageEntity]:
        """Update a selection stage"""
        try:
            stage_model = SelectionStageModel.objects.get(id=stage_id)
            
            # Update fields
            for field, value in stage_data.items():
                if hasattr(stage_model, field):
                    setattr(stage_model, field, value)
            
            stage_model.save()
            return self._model_to_entity(stage_model)
        
        except SelectionStageModel.DoesNotExist:
            return None
        
    def delete_stage(self, stage_id: str) -> bool:
        """Delete a selection stage (soft delete)"""
        try:
            stage_model = SelectionStageModel.objects.get(id=stage_id)
            
            # Only non-default stages can be deleted
            if stage_model.is_default:
                return False
            
            # Soft delete
            stage_model.is_active = False
            stage_model.save()
            return True
        
        except SelectionStageModel.DoesNotExist:
            return False
    
    def get_inactive_stages(self) -> List[SelectionStageEntity]:
        stages = SelectionStageModel.objects.filter(is_active=False).order_by('-updated_at')
        return [self._model_to_entity(stage) for stage in stages]
    
    def reactivate_stage(self, stage_id: int) -> Optional[SelectionStageEntity]:
        """Reactivate an inactive stage"""
        try:
            stage_model = SelectionStageModel.objects.get(id=stage_id)
            
            if stage_model.is_active:
                return None  # Already active
            
            stage_model.is_active = True
            stage_model.save()
            return self._model_to_entity(stage_model)
        
        except SelectionStageModel.DoesNotExist:
            return None
        
    def _model_to_entity(self, model: SelectionStageModel) -> SelectionStageEntity:
        """Convert model to entity"""
        return SelectionStageEntity(
            id=model.id,  # ✅ Integer ID
            slug=model.slug,  # ✅ Human-readable slug
            name=model.name,
            description=model.description,
            icon=model.icon,
            duration=model.duration,
            requires_premium=model.requires_premium,
            tier=model.tier,
            is_default=model.is_default,
            order=model.order,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )