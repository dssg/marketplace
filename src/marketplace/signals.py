import allauth.socialaccount.signals
import django.db.models.signals
from django.dispatch import receiver

from marketplace.domain import marketplace
from marketplace.models.user import User, UserType


@receiver(django.db.models.signals.post_save, sender=User)
def create_volunteer_profile(instance, created, raw, **_kwargs):
    """Create a volunteer profile for any new volunteer user."""
    if created and not raw and instance.initial_type == UserType.VOLUNTEER:
        marketplace.user.volunteer.ensure_profile(instance)


@receiver(allauth.socialaccount.signals.pre_social_login)
def process_social_login(request, sociallogin, **_kwargs):
    """Ensure validity of user to be created from a social login."""
    user = sociallogin.user

    # Set username #
    if user.email and not user.username:
        # Set reasonable username for new user
        # (socialaccount does not base this on email address)
        #
        # TODO: handle collisions?
        # socialaccount does, but then you get that lame username.
        user.username = user.email.split('@', 1)[0]

    # Assign user type (requested pre-OAuth) #
    user_type = request.session.pop('oauth_signup_usertype', None)

    if not user.pk:
        # New user was generated from social account profile;
        # ensure initial type setting reflects user's selection.
        if user_type == 'volunteer':
            user.initial_type = UserType.VOLUNTEER
        elif user_type == 'organization':
            user.initial_type = UserType.ORGANIZATION
        else:
            # No (valid) type was requested (that we can tell).
            # This could be a "log in" on a user account that never signed up.
            #
            # Rather than redirect them to choose NOW (and risk losing social
            # data or worse trust them to post it back),
            #
            # ...and rather than place an ephemeral flag in the session or set
            # something incorrect in the data,
            #
            # ...instead we'll set something "empty" in the database, and
            # expect a middleware to redirect them to insist that they make
            # their selection.
            #
            # User.initial_type defaults to the "volunteer" value, so we have to
            # be explicit that no selection has been made:
            user.initial_type = None
