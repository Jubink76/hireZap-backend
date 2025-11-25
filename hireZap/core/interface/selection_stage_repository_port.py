from abc import ABC, abstractmethod
from typing import List, Optional
from core.entities.selection_stage import SelectionStage

class SelectionStageRepositoryPort(ABC):

    @abstractmethod
    def create_stage(self, stage:SelectionStage) -> SelectionStage:
        """ Create new selection stage"""
        raise  NotImplementedError
    
    @abstractmethod
    def get_stage_by_id(self, stage_id:int) -> Optional[SelectionStage]:
        """ Get stages by id """
        raise NotImplementedError
    
    @abstractmethod
    def get_all_stages(self) -> List[SelectionStage]:
        """ Get all stages """
        raise NotImplementedError
    
    # @abstractmethod
    # def get_free_stages(self) -> List[SelectionStage]:
    #     """Get free stages """
    #     raise NotImplementedError
    
    # @abstractmethod
    # def get_premium_stages(self) -> List[SelectionStage]:
    #     """ Get premium stages """
    #     raise NotImplementedError
    
    @abstractmethod
    def update_stage(self,stage_id:int, stage_data:dict) -> Optional[SelectionStage]:
        """ Update stage"""
        raise NotImplementedError
    
    @abstractmethod
    def delete_stage(self,stage_id:int) -> bool:
        """ Delete a perticular stage"""
        raise NotImplementedError
    
    @abstractmethod
    def get_inactive_stages(self) -> List[SelectionStage]:
        """ Get inactive stages """
        raise NotImplementedError
    
    @abstractmethod
    def reactivate_stage(self, stage_id: int) -> Optional[SelectionStage]:
        """Reactivate an inactive stage"""
        raise NotImplementedError
    
    # @abstractmethod
    # def stage_exists(self,stage_id:int) -> bool:
    #     """ Check stage exist or not """
    #     raise NotImplementedError
    
    # @abstractmethod
    # def reorder_stages(self,stage_order:dict) -> bool:
    #     """ Reorder stages """
    #     raise NotImplementedError
    
