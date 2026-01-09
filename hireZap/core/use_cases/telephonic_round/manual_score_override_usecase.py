"""
core/use_cases/telephonic_round/manual_score_override_usecase.py
"""
from typing import Dict
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService


class ManualScoreOverrideUseCase:
    """
    Override AI-generated score with manual recruiter score
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
        interview_id: int,
        manual_score: int,
        manual_decision: str,
        override_reason: str,
        overridden_by_id: int
    ) -> Dict:
        """
        Override AI score with manual evaluation
        
        Args:
            interview_id: Interview ID
            manual_score: Manual score (0-100)
            manual_decision: Manual decision ('qualified' or 'not_qualified')
            override_reason: Reason for override
            overridden_by_id: ID of user making the override
        
        Returns:
            {
                'success': bool,
                'interview_id': int,
                'ai_score': int,
                'manual_score': int,
                'final_decision': str
            }
        """
        
        # 1. Get interview and performance result
        interview = self.repository.get_interview_by_id(interview_id)
        
        if not interview:
            return {
                'success': False,
                'error': 'Interview not found'
            }
        
        performance_result = self.repository.get_performance_result(interview_id)
        
        if not performance_result:
            return {
                'success': False,
                'error': 'No performance results found. Interview must be analyzed first.'
            }
        
        # 2. Validate manual score
        if not (0 <= manual_score <= 100):
            return {
                'success': False,
                'error': 'Score must be between 0 and 100'
            }
        
        # 3. Validate manual decision
        if manual_decision not in ['qualified', 'not_qualified']:
            return {
                'success': False,
                'error': "Decision must be 'qualified' or 'not_qualified'"
            }
        
        # 4. Store original AI values
        original_ai_score = performance_result.overall_score
        original_ai_decision = performance_result.decision
        
        # 5. Apply manual override
        updated_result = self.repository.update_manual_score(
            interview_id=interview_id,
            manual_score=manual_score,
            manual_decision=manual_decision,
            override_reason=override_reason,
            override_by_id=overridden_by_id
        )
        
        # 6. Update application status if decision changed
        if original_ai_decision != manual_decision:
            self._update_application_status(interview, manual_decision)
        
        # 7. Send notifications about override
        self._send_override_notifications(
            interview=interview,
            original_score=original_ai_score,
            new_score=manual_score,
            original_decision=original_ai_decision,
            new_decision=manual_decision,
            overridden_by_id=overridden_by_id
        )
        
        return {
            'success': True,
            'interview_id': interview_id,
            'ai_score': original_ai_score,
            'ai_decision': original_ai_decision,
            'manual_score': manual_score,
            'manual_decision': manual_decision,
            'final_score': updated_result.final_score,
            'final_decision': updated_result.final_decision,
            'message': 'Score override applied successfully'
        }
    
    def _update_application_status(self, interview, manual_decision: str):
        """Update application status based on manual decision"""
        application = interview.application
        
        if manual_decision == 'qualified':
            application.current_stage_status = 'qualified'
            application.status = 'qualified'
        else:
            application.current_stage_status = 'rejected'
            application.status = 'rejected'
        
        application.save()
    
    def _send_override_notifications(
        self,
        interview,
        original_score: int,
        new_score: int,
        original_decision: str,
        new_decision: str,
        overridden_by_id: int
    ):
        """Send notifications about score override"""
        
        # Notify recruiter who conducted the interview (if different from overrider)
        if interview.conducted_by_id and interview.conducted_by_id != overridden_by_id:
            self.notification_service.send_websocket_notification(
                user_id=interview.conducted_by_id,
                notification_type='score_overridden',
                data={
                    'interview_id': interview.id,
                    'candidate_name': f"{interview.application.first_name} {interview.application.last_name}",
                    'original_score': original_score,
                    'new_score': new_score,
                    'original_decision': original_decision,
                    'new_decision': new_decision,
                    'message': 'Interview score has been manually overridden'
                }
            )
        
        # Notify candidate if decision changed from rejected to qualified
        if original_decision == 'not_qualified' and new_decision == 'qualified':
            self.notification_service.send_websocket_notification(
                user_id=interview.application.candidate_id,
                notification_type='interview_status_updated',
                data={
                    'interview_id': interview.id,
                    'job_title': interview.job.job_title,
                    'decision': 'qualified',
                    'message': 'Good news! Your interview status has been updated to Qualified'
                }
            )
            
            # Send email
            self._send_status_update_email(interview, 'qualified')
        
        # Notify candidate if decision changed from qualified to rejected
        elif original_decision == 'qualified' and new_decision == 'not_qualified':
            self.notification_service.send_websocket_notification(
                user_id=interview.application.candidate_id,
                notification_type='interview_status_updated',
                data={
                    'interview_id': interview.id,
                    'job_title': interview.job.job_title,
                    'decision': 'not_qualified',
                    'message': 'Your interview status has been updated'
                }
            )
            
            # Send email
            self._send_status_update_email(interview, 'not_qualified')
    
    def _send_status_update_email(self, interview, new_decision: str):
        """Send email about status update"""
        from telephonic_round.tasks import send_status_update_email_task
        
        send_status_update_email_task.apply_async(
            args=[interview.id, new_decision],
            countdown=5
        )