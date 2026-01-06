from core.entities.application import Application
from core.interface.application_repository_port import ApplicationRepositoryPort
from typing import Optional, List
from application.models import ApplicationModel, ApplicationStageHistory
from selection_process.models import SelectionProcessModel
from django.utils import timezone
import logging

class ApplicationRepository(ApplicationRepositoryPort):
    
    def _model_to_entity(self, app_model: ApplicationModel) -> Application:
        """Convert Django model to entity"""
        job = getattr(app_model, 'job', None)
        candidate = getattr(app_model, 'candidate', None)
        screening_details = None
        screened_at = None
        try:
            if hasattr(app_model, 'screening_result'):
                result = app_model.screening_result
                screening_details = {
                    'matched_skills': result.matching_skills or [],
                    'missing_skills': result.missing_required_skills or [],
                    'matched_keywords': result.matched_keywords or [],
                    'experience_years': result.extracted_experience_years or 0,
                    'education': result.extracted_education or '',
                    'is_ats_friendly': result.is_ats_friendly,
                    'ats_issues': result.ats_issues or [],
                    'ai_summary': result.ai_summary or '',
                    'strengths': result.strengths or [],
                    'weaknesses': result.weaknesses or [],
                }
                screened_at = result.screening_at
        except Exception as e:
            logging.getLogger(__name__).debug(f"No screening result for application {app_model.id}: {e}")
        return Application(
            id=app_model.id,
            job_id=app_model.job_id,
            candidate_id=app_model.candidate_id,
            resume_url=app_model.resume_url,
            portfolio_url=app_model.portfolio_url,
            first_name=app_model.first_name,
            last_name=app_model.last_name,
            email=app_model.email,
            phone=app_model.phone,
            location=app_model.location,
            linkedin_profile=app_model.linkedin_profile,
            years_of_experience=app_model.years_of_experience,
            availability=app_model.availability,
            expected_salary=app_model.expected_salary,
            current_company=app_model.current_company,
            cover_letter=app_model.cover_letter,
            status=app_model.status,
            is_draft=app_model.is_draft,
            created_at=app_model.created_at,
            updated_at=app_model.updated_at,
            submitted_at=app_model.submitted_at,
            rejection_reason=app_model.rejection_reason,
            interview_date=app_model.interview_date,
            recruiter_notes=app_model.recruiter_notes,
            job_title=job.job_title if job else None,
            company_name=job.company.company_name if job and hasattr(job, 'company') else None,
            company_logo=app_model.job.company.logo_url if app_model.job.company else None,
            screening_status=app_model.screening_status,
            screening_decision=app_model.ats_decision or 'pending',
            screening_scores={
                'overall': app_model.ats_overall_score or 0,
                'skills': app_model.ats_skills_score or 0,
                'experience': app_model.ats_experience_score or 0,
                'education': app_model.ats_education_score or 0,
                'keywords': app_model.ats_keywords_score or 0,
            },
            screening_details=screening_details,
            screened_at=screened_at,
            current_stage_id=app_model.current_stage_id,
            current_stage_status=app_model.current_stage_status,
        )
    
    def create_application(self, application:Application) -> Optional[Application]:
        """Create a new job application"""
        try:
            first_stage_process = SelectionProcessModel.objects.filter(
                job_id=application.job_id,
                is_active=True
            ).order_by('order').first()

            app_model = ApplicationModel.objects.create(
                job_id=application.job_id,
                candidate_id=application.candidate_id,
                resume_url=application.resume_url,
                portfolio_url=application.portfolio_url,
                first_name=application.first_name,
                last_name=application.last_name,
                email=application.email,
                phone=application.phone,
                location=application.location,
                linkedin_profile=application.linkedin_profile,
                years_of_experience=application.years_of_experience,
                availability=application.availability,
                expected_salary=application.expected_salary,
                current_company=application.current_company,
                cover_letter=application.cover_letter,
                status=application.status,
                is_draft=application.is_draft,
                submitted_at=timezone.now() if not application.is_draft else None,
                current_stage=first_stage_process.stage if first_stage_process else None,
                current_stage_status='pending',
                screening_status='pending',
            )
            if first_stage_process and not application.is_draft:
                ApplicationStageHistory.objects.create(
                    application=app_model,
                    stage=first_stage_process.stage,
                    status='started',
                    started_at=timezone.now()
                )
            
            return self._model_to_entity(app_model)
        except Exception as e:
            return None

    def get_application_by_id(self, application_id: int) -> Optional[Application]:
        """Get application by ID"""
        try:
            app_model = ApplicationModel.objects.select_related('job', 'candidate').get(id=application_id)
            return self._model_to_entity(app_model)
        except ApplicationModel.DoesNotExist:
            return None

    def get_application_by_job_and_candidate(self, job_id: int, candidate_id: int) -> Optional[Application]:
        """Get application by job and candidate"""
        try:
            app_model = ApplicationModel.objects.get(
                job_id=job_id,
                candidate_id=candidate_id,
                is_draft=False  # Only get submitted applications
            )
            return self._model_to_entity(app_model)
        except ApplicationModel.DoesNotExist:
            return None

    def get_applications_by_candidate(self, candidate_id: int, include_drafts: bool = False):
        try:
            queryset = ApplicationModel.objects.filter(candidate_id=candidate_id)
            
            if not include_drafts:
                queryset = queryset.filter(is_draft=False)  # Changed from exclude(status='draft')
            
            app_models = queryset.select_related('job', 'candidate').order_by('-created_at')
            
            # Convert Django models to Application entities
            applications = []
            for app_model in app_models:
                try:
                    entity = self._model_to_entity(app_model)
                    applications.append(entity)
                except Exception as e:
                    return str(e)

            return applications  
        except Exception as e:
            return str(e)

    def get_applications_by_job(self, job_id: int) -> List[Application]:
        """Get all applications for a job"""
        try:
            # ✅ ADD select_related to load screening_result
            app_models = ApplicationModel.objects.filter(
                job_id=job_id,
                is_draft=False
            ).select_related(
                'candidate',
                'candidate__user',
                'job',
                'job__company',
                'screening_result',  # ✅ CRITICAL: Load screening details
                'current_stage'
            ).order_by('-created_at')
            
            return [self._model_to_entity(app) for app in app_models]
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error fetching applications: {e}")
            return []

    def get_applications_by_status(self, job_id: int, status: str) -> List[Application]:
        """Get applications by status for a specific job"""
        try:
            # ✅ ADD select_related here too
            app_models = ApplicationModel.objects.filter(
                job_id=job_id,
                status=status,
                is_draft=False
            ).select_related(
                'candidate',
                'candidate__user',
                'job',
                'job__company',
                'screening_result',  # ✅ CRITICAL: Load screening details
                'current_stage'
            ).order_by('-created_at')
            
            return [self._model_to_entity(app) for app in app_models]
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error fetching applications by status: {e}")
            return []

    def update_application(self, application_id: int, application_data: dict) -> Optional[Application]:
        """Update an application"""
        try:
            app_model = ApplicationModel.objects.get(id=application_id)
            
            # If converting from draft to submitted, set submitted_at
            if 'is_draft' in application_data and not application_data['is_draft'] and app_model.is_draft:
                application_data['submitted_at'] = timezone.now()
            
            for key, value in application_data.items():
                if hasattr(app_model, key):
                    setattr(app_model, key, value)
            
            app_model.save()
            return self._model_to_entity(app_model)
        except ApplicationModel.DoesNotExist:
            return None

    def update_application_status(self, application_id: int, status: str) -> Optional[Application]:
        """Update application status"""
        try:
            app_model = ApplicationModel.objects.get(id=application_id)
            app_model.status = status
            app_model.save()
            return self._model_to_entity(app_model)
        except ApplicationModel.DoesNotExist:
            return None

    def delete_application(self, application_id: int) -> bool:
        """Delete an application"""
        try:
            app_model = ApplicationModel.objects.get(id=application_id)
            app_model.delete()
            return True
        except ApplicationModel.DoesNotExist:
            return False

    def get_candidate_draft(self, candidate_id: int, job_id: int) -> Optional[Application]:
        """Get candidate's draft application for a specific job"""
        try:
            app_model = ApplicationModel.objects.get(
                candidate_id=candidate_id,
                job_id=job_id,
                is_draft=True
            )
            return self._model_to_entity(app_model)
        except ApplicationModel.DoesNotExist:
            return None