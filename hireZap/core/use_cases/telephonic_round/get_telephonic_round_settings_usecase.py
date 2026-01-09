from typing import Dict, List
from datetime import datetime
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort


class GetTelephonicRoundSettings():
    def __init__(self, repository:TelephonicRoundRepositoryPort):
        self.repository = repository
    
    def execute(self,job_id:int):
        settings = self.repository.get_settings_by_id(job_id)
        
        # Create default settings if none exist
        if not settings:
            settings = self.repository.create_default_settings(job_id)
            configured = False
        else:
            configured = True
        
        return {
            'success': True,
            'settings': self._serialize_settings(settings),
            'configured': configured
        }

    def _serialize_settings(self, settings) -> Dict:
        """Convert settings model to dictionary"""
        return {
            'id': settings.id,
            'job_id': settings.job_id,
            'communication_weight': settings.communication_weight,
            'technical_knowledge_weight': settings.technical_knowledge_weight,
            'problem_solving_weight': settings.problem_solving_weight,
            'enthusiasm_weight': settings.enthusiasm_weight,
            'clarity_weight': settings.clarity_weight,
            'professionalism_weight': settings.professionalism_weight,
            'minimum_qualifying_score': settings.minimum_qualifying_score,
            'auto_schedule_enabled': getattr(settings, 'auto_schedule_enabled', False),
            'default_duration_minutes': getattr(settings, 'default_duration_minutes', 30),
            'auto_send_notifications': getattr(settings, 'auto_send_notifications', True),
        }
        