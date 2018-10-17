import allauth.socialaccount.signals
import django.db.models.signals
from django.dispatch import receiver

from marketplace.domain import marketplace
from marketplace.models.user import User, UserType


@receiver(django.db.models.signals.post_save, sender=User)
def create_volunteer_profile(instance, created, raw, **_kwargs):
    if created and not raw and instance.initial_type == UserType.VOLUNTEER:
        marketplace.user.volunteer.ensure_profile(instance)


@receiver(allauth.socialaccount.signals.pre_social_login)
def process_social_login(request, sociallogin, **_kwargs):
    user = sociallogin.user

    # Set username #
    if user.email and not user.username:
        # Set reasonable username
        # (socialaccount does not base this on email address)
        #
        # TODO: handle collisions?
        # socialaccount does, but then you get that lame username.
        user.username = user.email.split('@', 1)[0]

    # Assign requested user type (pre-OAuth) #
    user_type = request.session.pop('oauth_signup_usertype', None)

    if not sociallogin.is_existing:
        if user_type == 'volunteer':
            user.initial_type = UserType.VOLUNTEER
        elif user_type == 'organization':
            user.initial_type = UserType.ORGANIZATION
