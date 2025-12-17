from typing import Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class JobSelectionProcess:
    job_id:int 
    stage_id:int
    order:int
    is_active:bool
    id:Optional[int] = None
    created_at:Optional[datetime] = None
    updated_at:Optional[datetime] = None

    
    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'stage_id': self.stage_id,
            'order': self.order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }