from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class JobModel(models.Model):
    WORK_TYPE_CHOICES = [
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
        ('onsite', 'Onsite'),
    ]
    EMPLOYMENT_TYPE_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    ]
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    company = models.ForeignKey('companies.CompanyModel', on_delete=models.CASCADE,related_name='jobs')
    recruiter = models.ForeignKey(User,on_delete=models.CASCADE,related_name='posted_jobs')
    job_title = models.CharField(max_length=255)
    location  = models.CharField(max_length=255)
    work_type = models.CharField(max_length=20,choices=WORK_TYPE_CHOICES)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)

    compensation_range = models.CharField(max_length=100, null=True, blank=True)
    posting_date = models.DateField(auto_now_add=True)
    cover_image = models.URLField(max_length=500, null=True, blank=True)
    role_summary = models.TextField(null=True, blank=True)
    skills_required = models.JSONField(default=list, blank=True)  # Store as JSON array
    key_responsibilities = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    benefits = models.TextField(null=True, blank=True)
    application_link = models.URLField(max_length=500, null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    applicants_visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recruiter', 'status']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', 'posting_date']),
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company.company_name}"
    


