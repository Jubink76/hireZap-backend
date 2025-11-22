from django.db import models
from django.conf import settings
from job.models import JobModel
from candidate.models import CandidateProfile


class ApplicationModel(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('qualified', 'Next round qualified'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('hired', 'Hired'),
    ]

    job = models.ForeignKey(JobModel, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE,related_name='applications')
    # Resume & Portfolio
    resume_url = models.URLField(max_length=1024, blank=True, null=True)
    portfolio_url = models.URLField(max_length=1024, blank=True, null=True)

    # Personal Information (cached from user profile or updated)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    linkedin_profile = models.URLField(max_length=500, blank=True, null=True)

    # Professional Details
    years_of_experience = models.CharField(max_length=20, blank=True, null=True)  # "0-2", "3-5", "5-7", "7+"
    availability = models.CharField(max_length=50, blank=True, null=True)  # "immediate", "2-weeks", etc.
    expected_salary = models.CharField(max_length=100, blank=True, null=True)
    current_company = models.CharField(max_length=255, blank=True, null=True)

    # Cover Letter & Additional Info
    cover_letter = models.TextField(blank=True, null=True)

    # Application Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='applied', db_index=True)
    rejection_reason = models.TextField(blank=True, null=True)
    interview_date = models.DateTimeField(blank=True, null=True)
    recruiter_notes = models.TextField(blank=True, null=True)

    # Draft Support
    is_draft = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True,db_index=True)  # When actually submitted (not draft)

    class Meta:
        db_table = 'applications'
        ordering = ['-created_at']
        unique_together = ['job', 'candidate']  # Prevent duplicate applications
        indexes = [
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['job', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['status','submitted_at']),
        ]

    def __str__(self):
        return f"{self.candidate.get_full_name()} - {self.job.job_title} ({self.status})"