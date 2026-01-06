from typing import Dict
from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort
from core.interface.ats_configuration_repository_port import ATSConfigurationRepositoryPort
from core.interface.notification_service_port import NotificationServicePort
from infrastructure.services.resume_screening_service import ResumeScreeningService


class ScreenResumeUseCase:
    """Use case for screening a single resume"""
    
    def __init__(
        self,
        screening_repo: ResumeScreeningRepositoryPort,
        ats_repo: ATSConfigurationRepositoryPort,
        notification_service: NotificationServicePort
    ):
        self.screening_repo = screening_repo
        self.ats_repo = ats_repo
        self.notification_service = notification_service
        self.screening_service = ResumeScreeningService()
    
    def execute(self, application_id: int) -> Dict:
        """Execute resume screening for one application"""
        
        # 1. Get application
        application = self.screening_repo.get_application_by_id(application_id)
        if not application:
            return {
                'success': False,
                'error': f'Application {application_id} not found'
            }
        
        # 2. Update status to processing
        self.screening_repo.update_screening_status(application_id, 'processing')
        
        # 3. Get ATS configuration
        ats_config = self.ats_repo.get_by_job_id(application.job.id)
        config_dict = self._build_ats_config_dict(ats_config, application.job)
        
        # 4. Get job requirements
        job_requirements = {
            'skills_required': application.job.skills_required,
            'key_responsibilities': application.job.key_responsibilities,
            'requirements': application.job.requirements,
        }
        
        # 5. Screen resume
        result = self.screening_service.screen_resume(
            resume_url=application.resume_url,
            ats_config=config_dict,
            job_requirements=job_requirements
        )
        
        if not result['success']:
            return result
        
        # 6. Save results
        save_success = self.screening_repo.save_screening_results(application_id, result)
        if not save_success:
            return {
                'success': False,
                'error': 'Failed to save screening results'
            }
        
        # 7. Update job progress
        self.screening_repo.update_job_progress(application.job.id)
        
        # 8. Send notifications
        self._send_notifications(application, result)
        
        return {
            'success': True,
            'application_id': application_id,
            'score': result['scores']['overall'],
            'decision': result['decision']
        }
    
    def _build_ats_config_dict(self, ats_config, job) -> Dict:
        """Build ATS config dictionary"""
        if ats_config:
            return {
                'skills_weight': ats_config.skills_weight,
                'experience_weight': ats_config.experience_weight,
                'education_weight': ats_config.education_weight,
                'keywords_weight': ats_config.keywords_weight,
                'passing_score': ats_config.passing_score,
                'required_skills': ats_config.required_skills,
                'preferred_skills': ats_config.preferred_skills,
                'minimum_experience_years': ats_config.minimum_experience_years,
                'required_education': ats_config.required_education,
                'important_keywords': ats_config.important_keywords,
                'auto_rejection_missing_skills': ats_config.auto_rejection_missing_skills,
                'auto_reject_below_experience': ats_config.auto_reject_below_experience,
            }
        else:
            # Default config
            return {
                'skills_weight': 40,
                'experience_weight': 30,
                'education_weight': 20,
                'keywords_weight': 10,
                'passing_score': 60,
                'required_skills': job.skills_required,
                'preferred_skills': [],
                'minimum_experience_years': 0,
                'required_education': None,
                'important_keywords': [],
                'auto_rejection_missing_skills': False,
                'auto_reject_below_experience': False,
            }
    
    def _send_notifications(self, application, result):
        """Send all notifications"""
        # Candidate notification
        self.notification_service.send_websocket_notification(
            user_id=application.candidate.user.id,
            notification_type='resume_screening_completed',
            data={
                'application_id': application.id,
                'job_title': application.job.job_title,
                'decision': result['decision'],
                'score': result['scores']['overall'],
            }
        )
        
        # Recruiter notification
        self.notification_service.send_websocket_notification(
            user_id=application.job.recruiter.id,
            notification_type='screening_progress_update',
            data={
                'job_id': application.job.id,
                'screened_count': self.screening_repo.get_job_by_id(application.job.id).screened_applications_count,
                'total_count': self.screening_repo.get_job_by_id(application.job.id).total_applications_count,
            }
        )
        
        # Email notification
        self.notification_service.send_screening_result_email(
            application_id=application.id,
            decision=result['decision'],
            score=result['scores']['overall']
        )