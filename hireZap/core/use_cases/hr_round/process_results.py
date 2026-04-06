from typing import Dict, List
from django.utils import timezone
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.repositories.hr_round_repository import HRInterviewRepository
from infrastructure.services.notification_service import NotificationService
import logging
logger = logging.getLogger(__name__)

class ProcessInterviewResultUseCase:
    
    def __init__(self):
        self.finalize_use_case = FinalizeResultUseCase()
        self.move_stage_use_case = MoveToNextStageUseCase()
    
    def finalize_result(self, *args, **kwargs) -> Dict:
        return self.finalize_use_case.execute(*args, **kwargs)
    
    def move_to_next_stage(self, *args, **kwargs) -> Dict:
        return self.move_stage_use_case.execute(*args, **kwargs)
    

class FinalizeResultUseCase:
    
    def __init__(self):
        self.repo = HRInterviewRepository()
        self.notification_service = NotificationService()
    
    def execute(
        self,
        interview_id: int,
        decision: str,
        decided_by_id: int,
        decision_reason: str = None,
        next_steps: str = None) -> Dict:
        try:
            interview = self.repo.get_interview_by_id(interview_id)
            notes = self.repo.get_notes_by_interview(interview_id)
            
            if not interview:
                return {'success': False, 'error': 'Interview not found'}
            
            if not notes:
                return {
                    'success': False,
                    'error': 'Notes must be completed before finalizing result'
                }
            
            if not notes.is_finalized:
                return {
                    'success': False,
                    'error': 'Notes must be finalized before making decision'
                }
            
            # Validate decision
            if decision not in ['qualified', 'not_qualified']:
                return {
                    'success': False,
                    'error': 'Decision must be either "qualified" or "not_qualified"'
                }
            
            # Get final score from notes
            final_score = notes.calculated_score or 0
            
            # Check if score meets minimum threshold
            settings = self.repo.get_settings_by_id(interview.job_id)
            if settings and decision == 'qualified':
                min_score = settings.minimum_qualifying_score
                if final_score < min_score:
                    return {
                        'success': False,
                        'error': f'Score {final_score} is below minimum threshold {min_score}'
                    }
            
            # Create result
            result = self.repo.create_or_update_result(
                interview_id=interview_id,
                final_score=final_score,
                decision=decision,
                decided_by_id=decided_by_id,
                decision_reason=decision_reason,
                next_steps=next_steps
            )
            
            # Update application status
            application = interview.application
            
            if decision == 'qualified':
                application.current_stage_status = 'qualified'
                application.status = 'qualified'
            else:
                application.current_stage_status = 'rejected'
                application.status = 'rejected'
            
            application.save(update_fields=['current_stage_status', 'status', 'updated_at'])
            
            from application.models import ApplicationStageHistory
            history_status = 'qualified' if decision == 'qualified' else 'rejected'

            ApplicationStageHistory.objects.filter(
                application=application,
                stage=interview.stage,
            ).update(
                status=history_status,
                completed_at=timezone.now(),
                feedback=decision_reason or '',
            )
            # Send notifications
            self._send_result_notifications(interview, result)
            
            # Send email
            from hr_round.tasks import send_hr_interview_result_email_task
            send_hr_interview_result_email_task.delay(interview_id)
            
            logger.info(f" Result finalized for interview {interview_id}: {decision} - {final_score}/100")
            
            return {
                'success': True,
                'result': result,
                'application': application
            }
            
        except Exception as e:
            logger.error(f" Finalize result error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_result_notifications(self, interview, result):
        # To candidate
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_result',
            data={
                'interview_id': interview.id,
                'type': 'hr_interview',
                'job_title': interview.job.job_title,
                'decision': result.decision,
                'score': result.final_score,
                'message': f"Your HR interview result is ready"
            }
        )
        
        # To recruiter
        self.notification_service.send_websocket_notification(
            user_id=interview.conducted_by_id,
            notification_type='interview_result_finalized',
            data={
                'interview_id': interview.id,
                'candidate_name': interview.candidate_name,
                'decision': result.decision,
                'score': result.final_score,
                'message': f'Result finalized for {interview.candidate_name}'
            }
        )


class MoveToNextStageUseCase:
    
    def __init__(self,
                repository:HRRoundRepositoryPort,
                notification_service:NotificationService):
        self.repository = repository
        self.notification_service = notification_service
    
    def execute(
        self,
        interview_ids: List[int],
        feedback: str = 'Passed HR round') -> Dict:

        if not interview_ids:
            return {'success': False, 'error': 'No interviews selected'}

        # 1. Validate all interviews
        validation = self._validate_interviews(interview_ids)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error'],
                'invalid_interviews': validation.get('invalid_interviews', [])
            }

        # 2. Move via repository (same as telephonic)
        try:
            moved_count = self.repository.move_to_next_stage(
                interview_ids=interview_ids,
                feedback=feedback
            )
        except Exception as e:
            logger.error(f"move_to_next_stage repository error: {str(e)}")
            return {'success': False, 'error': f'Failed to move candidates: {str(e)}'}

        # 3. Get next stage name for response
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

    def _validate_interviews(self, interview_ids: List[int]) -> Dict:
        invalid = []

        for interview_id in interview_ids:
            interview = self.repository.get_interview_by_id(interview_id)

            if not interview:
                invalid.append({'interview_id': interview_id, 'reason': 'Interview not found'})
                continue

            if interview.status != 'completed':
                invalid.append({
                    'interview_id': interview_id,
                    'reason': f'Interview not completed. Status: {interview.status}'
                })
                continue

            result = self.repository.get_result_by_interview(interview_id)
            if not result:
                invalid.append({'interview_id': interview_id, 'reason': 'No result found'})
                continue

            if result.decision != 'qualified':
                invalid.append({
                    'interview_id': interview_id,
                    'reason': f'Candidate not qualified. Decision: {result.decision}'
                })

        if invalid:
            return {
                'valid': False,
                'error': f'{len(invalid)} interview(s) cannot be moved',
                'invalid_interviews': invalid
            }

        return {'valid': True}

    def _get_next_stage_name(self, sample_interview_id: int) -> str:
        """Get next stage name from a sample interview for the response message."""
        try:
            interview = self.repository.get_interview_by_id(sample_interview_id)
            if interview and interview.application.current_stage:
                return interview.application.current_stage.name
            return 'Next Stage'
        except Exception:
            return 'Next Stage'

    def _send_stage_transition_notifications(
        self,
        interview_ids: List[int],
        next_stage_name: str
    ):
        for interview_id in interview_ids:
            try:
                interview = self.repository.get_interview_by_id(interview_id)
                if not interview:
                    continue

                # WebSocket
                self.notification_service.send_websocket_notification(
                    user_id=interview.application.candidate_id,
                    notification_type='stage_progression',
                    data={
                        'application_id': interview.application.id,
                        'job_title':      interview.job.job_title,
                        'previous_stage': 'HR Round',
                        'next_stage':     next_stage_name,
                        'message':        f"Congratulations! You've been moved to {next_stage_name}"
                    }
                )

                # Email (async)
                self._send_progression_email(interview, next_stage_name)

            except Exception as e:
                logger.error(f"Failed to notify candidate for interview {interview_id}: {str(e)}")

    def _send_progression_email(self, interview, next_stage_name: str):
        try:
            from hr_round.tasks import send_stage_progression_email
            send_stage_progression_email.apply_async(
                args=[interview.id, next_stage_name],
                countdown=5
            )
        except Exception as e:
            logger.error(f"Email task failed for interview {interview.id}: {str(e)}")