from django.db import models
from job.models import JobModel
from application.models import ApplicationModel

# Create your models here.
class ATSConfiguration(models.Model):
    """ATS scoring rules per job"""
    job = models.OneToOneField(JobModel, on_delete=models.CASCADE, related_name='ats_config')
    skills_weight = models.IntegerField(default=40) 
    experience_weight = models.IntegerField(default=30)
    education_weight = models.IntegerField(default=20)
    keywords_weight = models.IntegerField(default=10)
    #pass or fail threshold
    passing_score = models.IntegerField(default=60)
    #specific requirements
    required_skills = models.JSONField(default=list)
    preferred_skills = models.JSONField(default=list)
    minimum_experience_years = models.IntegerField(default=0)
    required_education = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    important_keywords = models.JSONField(default=list)
    auto_rejection_missing_skills = models.BooleanField(default=False)
    auto_reject_below_experience = models.BooleanField(default =False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ats_configurations'

    def __str__(self):
        return f"ATS Config - {self.job.job_title}"
    

class ResumeScreeningResult(models.Model):
    """Detailed ATS screening results"""
    application = models.OneToOneField(
        ApplicationModel,
        on_delete=models.CASCADE,
        related_name = 'screening_result'
    )
    # Detailed breakdown
    matching_skills =  models.JSONField(default=list)
    missing_required_skills = models.JSONField(default=list)
    matched_keywords = models.JSONField(default=list)

    extracted_experience_years = models.FloatField(null=True, blank=True)
    experience_meets_requirement = models.BooleanField(default=False)

    extracted_education = models.CharField(max_length=200, blank=True, null=True)
    education_meets_requirement = models.BooleanField(default=False)

    is_ats_friendly = models.BooleanField(default=True)
    ats_issues = models.JSONField(default=list)

    ai_summary = models.TextField(blank=True, null=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    recommendation_notes = models.TextField(blank=True, null=True)

    failure_reason = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    processing_time_seconds = models.FloatField(null=True, blank=True)
    screening_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'resume_screening_results'
    
    def __str__(self):
        return f"Screening result - {self.application.candidate.get_full_name()}"