from django.db import IntegrityError, transaction

from ..models.common import (
    ReviewStatus,
)
from ..models.user import (
    User, VolunteerProfile, VolunteerSkill,
)

class UserService():
    @staticmethod
    def get_user(request_user, userid):
        return User.objects.get(pk=userid)

    @staticmethod
    def get_all_volunteer_profiles(request_user):
        return VolunteerProfile.objects.filter(volunteer_status=ReviewStatus.ACCEPTED).order_by('user__first_name', 'user__last_name')

    @staticmethod
    def save_user(request_user, user_pk, user):  # TODO check the integrity of all the primary keys
        user.save()

    @staticmethod
    def create_volunteer_profile(request_user, user_pk):  # TODO check the integrity of all the primary keys
        # TODO check both users are the same
        if not VolunteerProfile.objects.filter(user=request_user).exists():
            volunteer_profile = VolunteerProfile()
            volunteer_profile.user = request_user
            try:
                volunteer_profile.save()
            except IntegrityError:
                raise ValueError('User already has a volunteer profile')

    @staticmethod
    def save_volunteer_profile(request_user, volunteer_pk, volunteer_profile):  # TODO check the integrity of all the primary keys
        volunteer_profile.save()

    @staticmethod
    def add_volunteer_skill(request_user, user_pk, volunteer_skill):  # TODO check the integrity of all the primary keys
        volunteer_skill.user = UserService.get_user(request_user, user_pk)
        try:
            volunteer_skill.save()
        except IntegrityError:
            raise ValueError('User already has skill')

    @staticmethod
    def get_volunteer_skills(request_user, user_pk):
        return VolunteerSkill.objects.filter(user__id = user_pk)

    @staticmethod
    def save_volunteer_skill(request_user, user_pk, skill_pk, volunteer_skill):  # TODO check the integrity of all the primary keys
        volunteer_skill.save()

    @staticmethod
    def delete_volunteer_skill(request_user, user_pk, skill_pk, volunteer_skill):  # TODO check the integrity of all the primary keys
        volunteer_skill.delete()
