from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class SubscriptionPlan:
    name: str
    price: float
    period: str
    description: str
    features: List[Dict]
    button_text: str
    card_color: str
    user_type : str #recruiter / candidate
    badge: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


    def to_dict(self) -> dict:
        """ Convert entity to dictionary"""
        return {
            'id' : self.id,
            'name': self.name,
            'price': self.price,
            'period': self.period,
            'description':self.description,
            'features':self.features,
            'buttonText':self.button_text,
            'cardColor':self.card_color,
            'userType':self.user_type,
            'badge':self.badge,
            'isDefault':self.is_default,
            'isActive':self.is_active,
            'created_at':self.created_at.isoformat() if self.created_at else None,
            'updated_at':self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_free(self) -> bool:
        """Check if plan is free"""
        return self.price == 0