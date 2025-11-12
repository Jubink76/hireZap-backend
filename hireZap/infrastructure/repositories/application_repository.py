from core.entities.application import Application
from core.interface.application_repository_port import ApplicationRepositoryPort
from typing import Optional, List
from application.models import ApplicationModel
from django.utils import timezone

class ApplicationRepository(ApplicationRepositoryPort):
    
    def _model_to_entity(self, app_model: ApplicationModel) -> Application:
        """Convert Django model to entity"""
        job = getattr(app_model, 'job', None)
        candidate = getattr(app_model, 'candidate', None)

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
        )
    
    def create_application(self, application:Application) -> Optional[Application]:
        """Create a new job application"""
        try:
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
            app_models = ApplicationModel.objects.filter(
                job_id=job_id,
                is_draft=False
            ).select_related('candidate')
            return [self._model_to_entity(app) for app in app_models]
        except Exception:
            return []

    def get_applications_by_status(self, job_id: int, status: str) -> List[Application]:
        """Get applications by status for a specific job"""
        try:
            app_models = ApplicationModel.objects.filter(
                job_id=job_id,
                status=status,
                is_draft=False
            ).select_related('candidate')
            return [self._model_to_entity(app) for app in app_models]
        except Exception:
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