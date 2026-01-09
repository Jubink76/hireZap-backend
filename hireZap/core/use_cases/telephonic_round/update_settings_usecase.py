"""
core/use_cases/telephonic_round/update_settings_usecase.py
"""
from typing import Dict
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort


class UpdateSettingsUseCase:
    
    """Update telephonic round settings for a job"""
    
    def __init__(self, repository: TelephonicRoundRepositoryPort):
        self.repository = repository
    
    def execute(self, job_id: int, settings_data: Dict) -> Dict:

        # Validate weights sum to 100
        weights = [
            settings_data.get('communication_weight', 0),
            settings_data.get('technical_knowledge_weight', 0),
            settings_data.get('problem_solving_weight', 0),
            settings_data.get('enthusiasm_weight', 0),
            settings_data.get('clarity_weight', 0),
            settings_data.get('professionalism_weight', 0),
        ]
        
        total_weight = sum(weights)
        if total_weight != 100:
            return {
                'success': False,
                'error': f'Weights must sum to 100. Current sum: {total_weight}'
            }
        
        # Validate minimum qualifying score
        min_score = settings_data.get('minimum_qualifying_score', 60)
        if not (0 <= min_score <= 100):
            return {
                'success': False,
                'error': 'Minimum qualifying score must be between 0 and 100'
            }
        
        # Update settings
        try:
            settings = self.repository.update_settings(job_id, settings_data)
            
            return {
                'success': True,
                'settings': self._serialize_settings(settings),
                'message': 'Settings updated successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update settings: {str(e)}'
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