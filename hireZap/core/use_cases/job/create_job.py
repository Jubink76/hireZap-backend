from core.entities.job import Job
from core.interface.job_repository_port import JobRepositoryPort
from typing import Dict, Any

class CreateJobUseCase:
    def __init__(self, job_repository: JobRepositoryPort):
        self.job_repository = job_repository
    
    def execute(self, recruiter_id: int, company_id: int, job_data: dict) -> Dict[str, Any]:
        # Construct Job entity from input data
        job = Job(
            recruiter_id=recruiter_id,
            company_id=company_id,
            job_title=job_data.get("job_title"),
            location=job_data.get("location"),
            work_type=job_data.get("work_type"),
            employment_type=job_data.get("employment_type"),
            compensation_range=job_data.get("compensation_range"),
            posting_date=job_data.get("posting_date"),
            cover_image=job_data.get("cover_image"),
            role_summary=job_data.get("role_summary"),
            skills_required=job_data.get("skills_required"),
            key_responsibilities=job_data.get("key_responsibilities"),
            requirements=job_data.get("requirements"),
            benefits=job_data.get("benefits"),
            application_link=job_data.get("application_link"),
            application_deadline=job_data.get("application_deadline"),
            applicants_visibility=job_data.get("applicants_visibility"),
            status=job_data.get("status", "active")  
        )

        # Create the job using the repository
        created_job = self.job_repository.create_job(job)

        if not created_job:
            return {
                "success": False,
                "error": "Failed to create job"
            }

        return {
            "success": True,
            "message": "Job created successfully",
            "job": created_job.to_dict()
        }
