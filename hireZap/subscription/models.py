from django.db import models
from django.core.validators import MinValueValidator


class SubscriptionPlanModel(models.Model):
    """Subscription plan models for recruiters and candidates"""
    USER_TYPE_CHOICES = [
        ('recruiter','Recruiter'),
        ('candidate','Candidate')
    ]

    PERIOD_CHOICES = [
        ('month','Monthly'),
        ('3 months', '3 Months'),
        ('6 months', '6 Months'),
        ('year', 'Yearly'),
        ('per post', 'Per Post'),
    ]

    CARD_COLOR_CHOICES = [
        ('cyan', 'Cyan'),
        ('emerald', 'Emerald'),
        ('gray', 'Gray'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField( max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='month')
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    button_text = models.CharField(max_length=50)
    card_color = models.CharField(max_length=20, choices=CARD_COLOR_CHOICES, default='cyan')
    user_type = models.CharField(max_length=20,choices=USER_TYPE_CHOICES)
    badge = models.CharField(max_length=50, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscripton_plans'
        ordering = ['price', 'created_at']
        indexes = [
            models.Index(fields=['user_type', 'is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.name} - {self.user_type} (₹{self.price}/{self.period})"
    
    def save(self, *args, **kwargs):
        # if this plan is set as default, remove default from others
        if self.is_default:
            SubscriptionPlanModel.objects.filter(
                user_type = self.user_type,
                is_default = True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

