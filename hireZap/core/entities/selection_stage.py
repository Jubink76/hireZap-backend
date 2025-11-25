from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class SelectionStage:
    id:int
    slug:str
    name: str
    description: str
    icon: str
    duration: str
    requires_premium: bool
    tier: str
    is_default: bool
    order: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            'id': self.id, 
            'slug': self.slug,  # Human-readable identifier
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'duration': self.duration,
            'requiresPremium': self.requires_premium,
            'tier': self.tier,
            'isDefault': self.is_default,
            'order': self.order,
            'isActive': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_free(self) -> bool:
        """Check if stage is free"""
        return self.tier == 'free' and not self.requires_premium
    
    def can_be_deleted(self) -> bool:
        """Check if stage can be deleted (non-default stages only)"""
        return not self.is_default