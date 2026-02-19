from typing import Dict
from django.utils import timezone
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
            
            application.save()
            
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
    
    def __init__(self):
        self.repo = HRInterviewRepository()
        self.notification_service = NotificationService()
    
    def execute(
        self,
        interview_id: int,
        next_stage_id: int = None) -> Dict:
        try:
            interview = self.repo.get_interview_by_id(interview_id)
            result = self.repo.get_result_by_interview(interview_id)
            
            if not interview or not result:
                return {'success': False, 'error': 'Interview or result not found'}
            
            if result.decision != 'qualified':
                return {
                    'success': False,
                    'error': 'Only qualified candidates can move to next stage'
                }
            
            application = interview.application
            
            # Get next stage
            if next_stage_id:
                from selection_process.models import SelectionStageModel
                next_stage = SelectionStageModel.objects.get(id=next_stage_id)
            else:
                # Find next stage automatically
                from selection_process.models import SelectionProcessModel
                
                current_process = SelectionProcessModel.objects.get(
                    job=interview.job,
                    stage=interview.stage
                )
                
                next_process = SelectionProcessModel.objects.filter(
                    job=interview.job,
                    order__gt=current_process.order,
                    is_active=True
                ).order_by('order').first()
                
                if not next_process:
                    return {
                        'success': False,
                        'error': 'No next stage found in selection process'
                    }
                
                next_stage = next_process.stage
            
            # Update application
            application.current_stage = next_stage
            application.current_stage_status = 'pending'
            application.save()
            
            # Create history record
            from application.models import ApplicationStageHistory
            ApplicationStageHistory.objects.create(
                application=application,
                stage=interview.stage,
                status='qualified',
                feedback=f"HR Interview Score: {result.final_score}/100",
                completed_at=timezone.now()
            )
            
            # Send notification
            self.notification_service.send_websocket_notification(
                user_id=application.candidate_id,
                notification_type='stage_progression',
                data={
                    'application_id': application.id,
                    'job_title': interview.job.job_title,
                    'current_stage': next_stage.name,
                    'message': f"Congratulations! You've moved to {next_stage.name}"
                }
            )
            
            # Send email
            from infrastructure.services.notification_service import NotificationService
            NotificationService().send_stage_progress_email(
                application_id=application.id,
                current_stage=interview.stage.name,
                next_stage=next_stage.name
            )
            
            logger.info(f" Candidate moved to {next_stage.name}")
            
            return {
                'success': True,
                'application': application,
                'next_stage': next_stage
            }
            
        except Exception as e:
            logger.error(f" Move to next stage error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }