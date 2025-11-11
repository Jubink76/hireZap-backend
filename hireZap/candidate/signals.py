from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CandidateProfile

@receiver(post_save,sender=settings.AUTH_USER_MODEL)
def create_candidate_profile(sender,instance,created,**kwargs):
    """ Automatically create candidate profile when a new user with role == 'candidate' is created """
    if created and instance.role == 'candidate':
        CandidateProfile.objects.create(
            user = instance,
            phone_number = instance.phone_number if hasattr(instance,'phone') else None,
            location = instance.location if hasattr(instance,'location') else None
        )