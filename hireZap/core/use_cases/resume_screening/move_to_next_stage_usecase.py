from typing import Dict, List
from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort
from core.interface.notification_service_port import NotificationServicePort

class MoveToNextStageUseCase:
    """Move qualified candidates to next stage"""
    
    def __init__(
        self,
        screening_repo: ResumeScreeningRepositoryPort,
        notification_service: NotificationServicePort
    ):
        self.screening_repo = screening_repo
        self.notification_service = notification_service
    
    def execute(self, application_ids: List[int], feedback: str = None) -> Dict:
        """Move applications to next stage"""
        
        results = []
        
        for app_id in application_ids:
            result = self._move_single_application(app_id, feedback)
            results.append(result)
        
        successful_moves = [r for r in results if r['success']]
        
        return {
            'success': True,
            'results': results,
            'total_moved': len(successful_moves)
        }
    
    def _move_single_application(self, application_id: int, feedback: str) -> Dict:
        """Move single application to next stage"""
        try:
            # This will be implemented in repository
            result = self.screening_repo.move_to_next_stage(application_id, feedback)
            
            if result['success']:
                # Send notifications
                self.notification_service.send_stage_progress_email(
                    application_id=application_id,
                    current_stage=result['current_stage'],
                    next_stage=result['next_stage']
                )
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'application_id': application_id,
                'error': str(e)
            }