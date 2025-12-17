from django.db import models
from django.core.validators import MinValueValidator
from job.models import JobModel

class SelectionStageModel(models.Model):
    TIER_CHOICES = [
        ('free', 'Free'),
        ('per-post', 'Per Post'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    ICON_CHOICES = [
        ('FileText', 'File Text'),
        ('Phone', 'Phone'),
        ('Video', 'Video'),
        ('Users', 'Users'),
        ('CheckCircle', 'Check Circle'),
        ('Award', 'Award'),
        ('Briefcase', 'Briefcase'),
        ('Lock', 'Lock')
    ]
    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='FileText')
    duration = models.CharField(max_length=100, blank=True)
    requires_premium = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES,default='free')
    is_default = models.BooleanField(default=False)
    order = models.IntegerField(default=0,validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['tier', 'is_active']),
            models.Index(fields=['order']),
            models.Index(fields=['is_active'])
        ]
    def __str__(self):
        return f"{self.name} ({self.tier})"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class SelectionProcessModel(models.Model):
    job = models.ForeignKey(JobModel,on_delete=models.CASCADE, related_name='selection_stages')
    stage = models.ForeignKey(SelectionStageModel, on_delete=models.CASCADE, related_name='job_processes')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_selection_process'
        ordering = ['order']
        unique_together = ['job','stage']
        indexes = [
            models.Index(fields=['job', 'is_active']),
            models.Index(fields=['job', 'order']),
        ]

    def __str__(self):
        return f"{self.job.job_title} - {self.stage.name} (Order: {self.order})"
