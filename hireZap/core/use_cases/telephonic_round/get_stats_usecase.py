from typing import Dict
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort

class GetStatsUsecase:
    def __init__(self, repository:TelephonicRoundRepositoryPort):
        self.repository = repository

    def execute(self, job_id:int) -> Dict:
        try:
            stats = self.repository.get_job_interview_stats(job_id)
            # Calculate additional metrics
            total = stats.get('total_candidates', 0)
            completed = stats.get('completed', 0)
            qualified = stats.get('qualified', 0)
            
            # Calculate completion rate
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            # Calculate qualification rate
            qualification_rate = (qualified / completed * 100) if completed > 0 else 0
            
            # Add calculated metrics
            enhanced_stats = {
                **stats,
                'completion_rate': round(completion_rate, 2),
                'qualification_rate': round(qualification_rate, 2),
                'pending_count': stats.get('not_scheduled', 0) + stats.get('scheduled', 0),
            }
            
            return {
                'success': True,
                'stats': enhanced_stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to fetch statistics: {str(e)}'
            }