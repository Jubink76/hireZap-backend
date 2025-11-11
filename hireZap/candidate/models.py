from django.db import models
from django.conf import settings
from  django.core.validators import MinValueValidator, MaxValueValidator

class CandidateProfile(models.Model):
    """
        Candidate profile with OneToOne relationship to User
        user_id is the primary key, so candidate_id = user_id
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='candidate_profile'
    )
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    github_url = models.URLField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    resume_url = models.URLField(max_length=1024, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidates'
    
    def __str__(self):
        return f"{self.user.full_name}'s profile "
    
class CandidateEducation(models.Model):
    """Education records - candidate is the user_id"""
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='educations'
    )
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    start_year = models.IntegerField()
    end_year = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_education'
        ordering = ['-end_year', '-start_year']

    def __str__(self):
        return f"{self.degree} at {self.institution}"

class CandidateExperience(models.Model):
    """Work experience records - candidate is the user_id"""
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_experiences'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.role} at {self.company_name}"
    
class CandidateSkill(models.Model):
    """Skills - candidate is the user_id"""
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    skill_name = models.CharField(max_length=100)
    proficiency = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Proficiency level from 1 (beginner) to 5 (expert)"
    )
    years_of_experience = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_skills'
        unique_together = ['candidate', 'skill_name']
        ordering = ['-proficiency', 'skill_name']

    def __str__(self):
        return f"{self.skill_name} - {self.proficiency}/5 stars"
    
class CandidateCertification(models.Model):
    """Certifications - candidate is the user_id"""
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    credential_url = models.URLField(max_length=1024, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_certifications'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.name} from {self.issuer}"