# infrastructure/repositories/job_selection_process_repository.py

from typing import List, Optional
from core.interface.job_selection_process_repository_port import JobSelectionProcessRepositoryPort
from core.entities.selection_process import JobSelectionProcess as JobSelectionProcessEntity
from core.entities.selection_stage import SelectionStage as SelectionStageEntity
from selection_process.models import SelectionProcessModel, SelectionStageModel
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class JobSelectionProcessRepository(JobSelectionProcessRepositoryPort):
    
    @transaction.atomic
    def save_job_selection_process(self, job_id: int, stage_ids: List[int]) -> List[JobSelectionProcessEntity]:
        """Save selection stages for a job"""
        try:
            # Delete existing stages for this job
            SelectionProcessModel.objects.filter(job_id=job_id).delete()
            
            # Create new stages
            processes = []
            for order, stage_id in enumerate(stage_ids, start=1):
                process_model = SelectionProcessModel.objects.create(
                    job_id=job_id,
                    stage_id=stage_id,
                    order=order,
                    is_active=True
                )
                processes.append(self._model_to_entity(process_model))
            
            return processes
        except Exception as e:
            logger.error(f"Error saving job selection process: {str(e)}")
            raise
    
    def get_job_selection_processes(self, job_id: int) -> List[JobSelectionProcessEntity]:
        """Get all selection process records for a job"""
        try:
            processes = SelectionProcessModel.objects.filter(
                job_id=job_id,
                is_active=True
            ).order_by('order')
            
            return [self._model_to_entity(process) for process in processes]
        except Exception as e:
            logger.error(f"Error fetching job selection processes: {str(e)}")
            return []
    
    def get_job_selection_stages(self, job_id: int) -> List[SelectionStageEntity]:
        """Get all selection stages for a job with details"""
        try:
            processes = SelectionProcessModel.objects.filter(
                job_id=job_id,
                is_active=True
            ).select_related('stage').order_by('order')
            
            stages = []
            for process in processes:
                stage = process.stage
                # Create stage entity with order from process
                stage_entity = SelectionStageEntity(
                    id=stage.id,
                    slug=stage.slug,
                    name=stage.name,
                    description=stage.description,
                    icon=stage.icon,
                    duration=stage.duration,
                    requires_premium=stage.requires_premium,
                    tier=stage.tier,
                    is_default=stage.is_default,
                    order=process.order,  # Use order from job_selection_process
                    is_active=stage.is_active,
                    created_at=stage.created_at,
                    updated_at=stage.updated_at
                )
                stages.append(stage_entity)
            
            return stages
        except Exception as e:
            logger.error(f"Error fetching job selection stages: {str(e)}")
            return []
    
    def delete_job_selection_process(self, job_id: int) -> bool:
        """Delete all selection stages for a job"""
        try:
            SelectionProcessModel.objects.filter(job_id=job_id).delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting job selection process: {str(e)}")
            return False
    
    def job_has_stages(self, job_id: int) -> bool:
        """Check if job has configured stages"""
        return SelectionProcessModel.objects.filter(
            job_id=job_id,
            is_active=True
        ).exists()
    
    def update_stage_order(self, job_id: int, stage_id: int, new_order: int) -> Optional[JobSelectionProcessEntity]:
        """Update the order of a specific stage for a job"""
        try:
            process = SelectionProcessModel.objects.get(
                job_id=job_id,
                stage_id=stage_id,
                is_active=True
            )
            process.order = new_order
            process.save()
            return self._model_to_entity(process)
        except SelectionProcessModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error updating stage order: {str(e)}")
            return None
    
    def _model_to_entity(self, model: SelectionProcessModel) -> JobSelectionProcessEntity:
        """Convert model to entity"""
        return JobSelectionProcessEntity(
            id=model.id,
            job_id=model.job_id,
            stage_id=model.stage_id,
            order=model.order,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )