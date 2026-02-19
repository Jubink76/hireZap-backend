from typing import Dict
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.services.notification_service import NotificationService
import logging
logger = logging.getLogger(__name__)

class NotesManagementUseCase:
    
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        notification_service: NotificationService):
        
        self.repo = repository
        self.notification_service = notification_service
        self.create_use_case = CreateNotesUseCase(repository)
        self.update_use_case = UpdateNotesUseCase(repository)
        self.finalize_use_case = FinalizeNotesUseCase(repository, notification_service)
    
    def create_notes(self, *args, **kwargs) -> Dict:
        """Create notes - delegates to CreateNotesUseCase"""
        return self.create_use_case.execute(*args, **kwargs)
    
    def update_notes(self, *args, **kwargs) -> Dict:
        """Update notes - delegates to UpdateNotesUseCase"""
        return self.update_use_case.execute(*args, **kwargs)
    
    def finalize_notes(self, *args, **kwargs) -> Dict:
        """Finalize notes - delegates to FinalizeNotesUseCase"""
        return self.finalize_use_case.execute(*args, **kwargs)


class CreateNotesUseCase:
    
    def __init__(self, repository: HRRoundRepositoryPort):
        self.repo = repository
    
    def execute(
        self,
        interview_id: int,
        recorded_by_id: int,
        notes_data: Dict) -> Dict:
        try:
            interview = self.repo.get_interview_by_id(interview_id)
            
            if not interview:
                return {'success': False, 'error': 'Interview not found'}
            
            # Check if notes already exist
            existing_notes = self.repo.get_notes_by_interview(interview_id)
            if existing_notes:
                return {
                    'success': False,
                    'error': 'Notes already exist. Use update instead.'
                }
            
            # Create notes
            notes = self.repo.create_or_update_notes(
                interview_id=interview_id,
                recorded_by_id=recorded_by_id,
                notes_data=notes_data
            )
            
            logger.info(f"Notes created for interview {interview_id} - Score: {notes.calculated_score}")
            
            return {
                'success': True,
                'notes': notes
            }
            
        except Exception as e:
            logger.error(f"Create notes error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class UpdateNotesUseCase:
    
    def __init__(self, repository: HRRoundRepositoryPort):
        self.repo = repository
    
    def execute(
        self,
        interview_id: int,
        recorded_by_id: int,
        notes_data: Dict) -> Dict:
        
        try:
            # Check if notes exist
            existing_notes = self.repo.get_notes_by_interview(interview_id)
            
            if existing_notes and existing_notes.is_finalized:
                return {
                    'success': False,
                    'error': 'Notes are finalized and cannot be modified'
                }
            
            # Update notes
            notes = self.repo.create_or_update_notes(
                interview_id=interview_id,
                recorded_by_id=recorded_by_id,
                notes_data=notes_data
            )
            
            logger.info(f"Notes updated for interview {interview_id} - Score: {notes.calculated_score}")
            
            return {
                'success': True,
                'notes': notes
            }
            
        except Exception as e:
            logger.error(f"Update notes error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        

class FinalizeNotesUseCase:
    
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        notification_service: NotificationService):
        
        self.repo = repository
        self.notification_service = notification_service
    
    def execute(self, interview_id: int, finalized_by_id: int) -> Dict:
        try:
            notes = self.repo.get_notes_by_interview(interview_id)
            
            if not notes:
                return {'success': False, 'error': 'Notes not found'}
            
            if notes.is_finalized:
                return {'success': False, 'error': 'Notes already finalized'}
            
            # Validate all required sections are completed
            required_ratings = [
                notes.communication_rating,
                notes.culture_fit_rating,
                notes.motivation_rating,
                notes.professionalism_rating,
                notes.problem_solving_rating,
                notes.team_collaboration_rating
            ]
            
            if any(rating is None for rating in required_ratings):
                return {
                    'success': False,
                    'error': 'All section ratings must be completed before finalizing'
                }
            
            # Finalize notes
            notes = self.repo.finalize_notes(interview_id)
            
            # Send notification
            interview = self.repo.get_interview_by_id(interview_id)
            self.notification_service.send_websocket_notification(
                user_id=finalized_by_id,
                notification_type='notes_finalized',
                data={
                    'interview_id': interview_id,
                    'candidate_name': interview.candidate_name,
                    'final_score': notes.calculated_score,
                    'message': 'Interview notes finalized successfully'
                }
            )
            
            logger.info(f"Notes finalized for interview {interview_id}")
            
            return {
                'success': True,
                'notes': notes
            }
            
        except Exception as e:
            logger.error(f"Finalize notes error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }