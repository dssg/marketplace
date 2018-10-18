from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db import transaction

from marketplace.domain import marketplace


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Ensure validity of user created from social login.

    django-allauth handles authentication of users against OAuth
    providers. And when this proves to be an existing User, it's then
    largely just a matter of logging them in.

    In the case of the authentication of a new User, however, allauth
    populates a new User instance -- and otherwise without the
    involvement of this codebase. So the allauth-constructed User
    is pre- and post-processed here.

    """
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user

        # Set username #
        if user.email and not user.username:
            # Set reasonable username for new user
            # (socialaccount does not base this on email address)
            #
            # TODO: handle collisions?
            # socialaccount *does*, but then you get that lame username.
            user.username = user.email.split('@', 1)[0]

    @transaction.atomic
    def save_user(self, request, sociallogin, form=None):
        creation = not sociallogin.user.pk

        # Assign user type (requested pre-OAuth) #
        user_type = request.session.pop('oauth_signup_usertype', None)

        if creation:
            # New user was generated from social account profile;
            # ensure initial type setting reflects user's selection.
            try:
                marketplace.user.add_user_presave(sociallogin.user, user_type)
            except ValueError:
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
                sociallogin.user.initial_type = None

        user = super().save_user(request, sociallogin, form)

        # Assign user volunteer profile and preferences #
        task_preferences = request.session.pop('oauth_signup_preferences', None)

        if creation:
            marketplace.user.add_user_postsave(user, task_preferences)
