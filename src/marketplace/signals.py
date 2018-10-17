import django.db.models.signals
from django.dispatch import receiver

from marketplace.domain import marketplace
from marketplace.models.user import User, UserType


@receiver(django.db.models.signals.post_save, sender=User)
def create_volunteer_profile(instance, created, raw, **_kwargs):
    if created and not raw and instance.initial_type == UserType.VOLUNTEER:
        marketplace.user.volunteer.ensure_profile(instance)
