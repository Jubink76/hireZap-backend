from typing import Optional, List
import json
from core.entities.job import Job
from core.interface.job_repository_port import JobRepositoryPort
from job.models import JobModel

class JobRepository(JobRepositoryPort):
    def _model_to_entity(self,job_model:JobModel) -> Job:
        return Job(
            id=job_model.id,
            company_id=job_model.company_id,
            recruiter_id=job_model.recruiter_id,
            job_title=job_model.job_title,
            location=job_model.location,
            work_type=job_model.work_type,
            employment_type=job_model.employment_type,
            compensation_range=job_model.compensation_range,
            posting_date=job_model.posting_date,
            cover_image=job_model.cover_image,
            role_summary=job_model.role_summary,
            skills_required=json.dumps(job_model.skills_required) if job_model.skills_required else None,
            key_responsibilities=job_model.key_responsibilities,
            requirements=job_model.requirements,
            benefits=job_model.benefits,
            application_link=job_model.application_link,
            application_deadline=job_model.application_deadline,
            applicants_visibility=job_model.applicants_visibility,
            status=job_model.status,
            created_at=job_model.created_at,
            updated_at=job_model.updated_at,
        )
    
    def create_job(self,job_data:dict) -> Optional[Job]:
        try:
            # parse skills if it is json string
            if 'skills_required' in job_data and isinstance(job_data['skills_required'], str):
                job_data['skills_required'] = json.loads(job_data['skills_required'])

            job_model = JobModel.objects.create(**job_data)
            return self._model_to_entity(job_model)
        except Exception as e:
            print(f" Error creating in job: {str(e)}")
            return None
    
    def get_job_by_id(self, job_id:int) -> Optional[Job]:
        try:
            job_model = JobModel.objects.select_related('company','recruiter').get(id=job_id)
            return self._model_to_entity(job_model)
        except JobModel.DoesNotExist:
            return None
    
    def get_jobs_by_recruiter(self, recruiter_id:int) -> List[Job]:
        try:
            job_model = JobModel.objects.filter(recruiter_id=recruiter_id).select_related('company')
            return [self._model_to_entity(job) for job in job_model]
        except JobModel.DoesNotExist:
            return None
    
    def get_jobs_by_company(self, company_id:int) -> List[Job]:
        try:
            job_model = JobModel.objects.filter(company_id=company_id).select_related('recruiter')
            return [self._model_to_entity(job) for job in job_model]
        except JobModel.DoesNotExist:
            return None
    
    def update_job(self, job_id:int, job_data:dict) -> Optional[Job]:
        try:
            job_model = JobModel.objects.get(id=job_id)
            if 'skills_required' in job_data and isinstance(job_data['skills_required'],str):
                job_data['skills_required'] = json.loads(job_data['skills_required'])

            for key, value in job_data.items():
                if hasattr(job_model, key):
                    setattr(job_model,key,value)
            job_model.save()
            return self._model_to_entity(job_model)
        except JobModel.DoesNotExist:
            return None
    
    def delete_job(self, job_id) -> bool:
        try:
            job_model = JobModel.objects.get(id=job_id)
            job_model.delete()
            return True
        except JobModel.DoesNotExist:
            return False
    
    def get_all_active_jobs(self) -> List[Job]:
        try:
            job_model = JobModel.objects.filter(status = 'active').select_related('company','recruiter')
            return [self._model_to_entity(job) for job in job_model]
        except JobModel.DoesNotExist:
            return None
        
    def update_job_status(self, job_id:int, status:str) -> Optional[Job]:
        try:
            job_model = JobModel.objects.get(id=job_id)
            job_model.status = status
            job_model.save()
            return self._model_to_entity(job_model)
        except JobModel.DoesNotExist:
            return None
    
