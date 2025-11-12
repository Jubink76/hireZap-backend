from typing import Optional
from core.entities.application import Application
from core.interface.application_repository_port import ApplicationRepositoryPort

class CreateApplicationUsecase:
    def __init__(self,repository:ApplicationRepositoryPort):
        self.repository = repository
    
    def execute(self,application_data:dict) -> dict:
        try:
            existing_appliction = self.repository.get_application_by_job_and_candidate(
                application_data['job_id'],
                application_data['candidate_id']
            )
            if existing_appliction:
                return {
                    'success':False,
                    'error' : "You have already applied for this job"
                }
            draft = self.repository.get_candidate_draft(
                application_data['candidate_id'],
                application_data['job_id']
            )
            if draft and not application_data.get('is_draft', False):
                # Converting draft to submission
                updated_data = {**application_data, 'is_draft': False}
                application = self.repository.update_application(draft.id, updated_data)
            elif draft and application_data.get('is_draft', False):
                # Updating existing draft
                application = self.repository.update_application(draft.id, application_data)
            else:
                # Create new application
                application = Application(**application_data)
                application = self.repository.create_application(application)
            
            if not application:
                return {
                    'success' : False,
                    'error' : "Failed to create application"
                }
            return {
                'success':True,
                'data':application.to_dict(),
                'message': 'Draft saved successfully' if application.is_draft else 'Application submitted successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }