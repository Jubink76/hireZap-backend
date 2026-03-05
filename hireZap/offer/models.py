from django.db import models
from application.models import ApplicationModel
from django.conf import settings

class OfferLetterModel(models.Model):
    application = models.OneToOneField(
        ApplicationModel,
        on_delete=models.CASCADE,
        related_name='offer_letter'
    )
    position_title = models.CharField(max_length=250)
    offered_salary = models.CharField(max_length=100)
    joining_date = models.DateField()
    offer_expiry_date = models.DateField()
    custom_message = models.TextField(blank=True, null=True)
    offer_letter_url  = models.URLField(max_length=1024, blank=True, null=True)
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    status = models.CharField(max_length=250, choices=STATUS_CHOICES, default='sent', db_index=True)
    candidate_response_note = models.TextField(blank=True, null=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_offers'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'offer_letters'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['status', 'sent_at']),
        ]

    def __str__(self):
        return f"Offer -> {self.application}({self.status})"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.offer_expiry_date < timezone.now().date() and self.status == 'sent'