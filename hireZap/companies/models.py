from django.db import models
from django.conf import settings

class Company(models.Model):
    """Company model for storing recruiter company information"""
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    recruiter = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company',
        limit_choices_to={'role': 'recruiter'}
    )
    company_name = models.CharField(max_length=255, db_index=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    business_certificate = models.URLField(max_length=500, blank=True, null=True)   
    business_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50)
    website = models.URLField(max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    founded_year = models.CharField(max_length=4, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['verification_status','created_at']),
            models.Index(fields=['recruiter','verification_status']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.verification_status}"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'
    
    @property
    def is_pending(self):
        return self.verification_status == 'pending'