"""
core/use_cases/telephonic_round/move_to_next_stage_usecase.py
"""
from typing import Dict, List
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService


class MoveToNextStageUseCase:
    """
    Move qualified candidates to the next interview stage
    Similar to resume screening's move to next stage
    """
    
    def __init__(
        self,
        repository: TelephonicRoundRepositoryPort,
        notification_service: NotificationService
    ):
        self.repository = repository
        self.notification_service = notification_service
    
    def execute(
        self,
        interview_ids: List[int],
        feedback: str = 'Passed telephonic round'
    ) -> Dict:
        """
        Move candidates to next stage
        
        Args:
            interview_ids: List of interview IDs to move
            feedback: Feedback message for stage transition
        
        Returns:
            {
                'success': bool,
                'moved_count': int,
                'failed_count': int,
                'errors': list,
                'next_stage': str
            }
        """
        
        if not interview_ids:
            return {
                'success': False,
                'error': 'No interviews selected'
            }
        
        # 1. Validate all interviews are qualified
        validation_result = self._validate_interviews(interview_ids)
        
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'invalid_interviews': validation_result.get('invalid_interviews', [])
            }
        
        # 2. Move to next stage via repository
        try:
            moved_count = self.repository.move_to_next_stage(
                interview_ids=interview_ids,
                feedback=feedback
            )
            
            # 3. Get next stage info for response
            next_stage_name = self._get_next_stage_name(interview_ids[0])
            
            # 4. Send notifications
            self._send_stage_transition_notifications(
                interview_ids=interview_ids,
                next_stage_name=next_stage_name
            )
            
            return {
                'success': True,
                'moved_count': moved_count,
                'total': len(interview_ids),
                'next_stage': next_stage_name,
                'message': f'Successfully moved {moved_count} candidate(s) to {next_stage_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to move candidates: {str(e)}'
            }
    
    def _validate_interviews(self, interview_ids: List[int]) -> Dict:
        """
        Validate that all interviews can be moved to next stage
        """
        invalid_interviews = []
        
        for interview_id in interview_ids:
            interview = self.repository.get_interview_by_id(interview_id)
            
            if not interview:
                invalid_interviews.append({
                    'interview_id': interview_id,
                    'reason': 'Interview not found'
                })
                continue
            
            # Check if interview is completed
            if interview.status != 'completed':
                invalid_interviews.append({
                    'interview_id': interview_id,
                    'reason': f'Interview not completed. Status: {interview.status}'
                })
                continue
            
            # Check if performance result exists
            performance_result = self.repository.get_performance_result(interview_id)
            
            if not performance_result:
                invalid_interviews.append({
                    'interview_id': interview_id,
                    'reason': 'No performance results available'
                })
                continue
            
            # Check if decision is qualified
            if performance_result.final_decision != 'qualified':
                invalid_interviews.append({
                    'interview_id': interview_id,
                    'reason': f'Candidate not qualified. Decision: {performance_result.final_decision}'
                })
                continue
        
        if invalid_interviews:
            return {
                'valid': False,
                'error': f'{len(invalid_interviews)} interview(s) cannot be moved',
                'invalid_interviews': invalid_interviews
            }
        
        return {'valid': True}
    
    def _get_next_stage_name(self, sample_interview_id: int) -> str:
        """Get name of next stage"""
        try:
            interview = self.repository.get_interview_by_id(sample_interview_id)
            if interview and interview.application.current_stage:
                return interview.application.current_stage.name
            return 'Next Stage'
        except:
            return 'Next Stage'
    
    def _send_stage_transition_notifications(
        self,
        interview_ids: List[int],
        next_stage_name: str
    ):
        """Send notifications to candidates about stage progression"""
        
        for interview_id in interview_ids:
            try:
                interview = self.repository.get_interview_by_id(interview_id)
                
                if not interview:
                    continue
                
                # WebSocket notification
                self.notification_service.send_websocket_notification(
                    user_id=interview.application.candidate_id,
                    notification_type='stage_progression',
                    data={
                        'interview_id': interview_id,
                        'job_title': interview.job.job_title,
                        'previous_stage': 'Telephonic Round',
                        'next_stage': next_stage_name,
                        'message': f'Congratulations! You have been moved to {next_stage_name}'
                    }
                )
                
                # Email notification (async)
                self._send_progression_email(interview, next_stage_name)
                
            except Exception as e:
                print(f"❌ Failed to notify candidate for interview {interview_id}: {str(e)}")
    
    def _send_progression_email(self, interview, next_stage_name: str):
        """Trigger email about stage progression"""
        from telephonic_round.tasks import send_stage_progression_email
        
        send_stage_progression_email.apply_async(
            args=[interview.id, next_stage_name],
            countdown=5
        )