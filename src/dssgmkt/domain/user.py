from django.db import IntegrityError, transaction

from ..models.common import (
    ReviewStatus,
)
from ..models.user import (
    User, UserType, VolunteerProfile, VolunteerSkill,
)
from ..models.org import (
    OrganizationRole,
)

from .common import validate_consistent_keys
from .org import OrganizationService
from .proj import ProjectService, ProjectTaskService
from dssgmkt.authorization.common import ensure_user_has_permission

class UserService():
    @staticmethod
    def get_user(request_user, userid):
        return User.objects.get(pk=userid)

    @staticmethod
    def get_all_volunteer_profiles(request_user):
        return VolunteerProfile.objects.filter(volunteer_status=ReviewStatus.ACCEPTED).order_by('user__first_name', 'user__last_name')

    @staticmethod
    def save_user(request_user, user_pk, user):
        validate_consistent_keys(user, ('id', user_pk))
        user.save()

    @staticmethod
    def create_volunteer_profile(request_user, user_pk):
        target_user = UserService.get_user(request_user, user_pk)
        ensure_user_has_permission(request_user, target_user, 'user.is_same_user')
        # TODO check both users are the same
        if not VolunteerProfile.objects.filter(user=request_user).exists():
            volunteer_profile = VolunteerProfile()
            volunteer_profile.user = request_user
            try:
                volunteer_profile.save()
            except IntegrityError:
                raise ValueError('User already has a volunteer profile')

    @staticmethod
    def save_volunteer_profile(request_user, volunteer_pk, volunteer_profile):
        validate_consistent_keys(volunteer_profile, ('id', volunteer_pk))
        ensure_user_has_permission(request_user, volunteer_profile.user, 'user.is_same_user')
        volunteer_profile.save()

    @staticmethod
    def add_volunteer_skill(request_user, user_pk, volunteer_skill):
        target_user = UserService.get_user(request_user, user_pk)
        ensure_user_has_permission(request_user, target_user, 'user.is_same_user')
        volunteer_skill.user = target_user
        try:
            volunteer_skill.save()
        except IntegrityError:
            raise ValueError('User already has skill')

    @staticmethod
    def get_volunteer_skills(request_user, user_pk):
        return VolunteerSkill.objects.filter(user__id = user_pk)

    @staticmethod
    def save_volunteer_skill(request_user, user_pk, skill_pk, volunteer_skill):
        validate_consistent_keys(volunteer_skill, ('id', skill_pk), (['user','id'], user_pk))
        ensure_user_has_permission(request_user, volunteer_skill.user, 'user.is_same_user')
        volunteer_skill.save()

    @staticmethod
    def delete_volunteer_skill(request_user, user_pk, skill_pk, volunteer_skill):
        validate_consistent_keys(volunteer_skill, ('id', skill_pk), (['user','id'], user_pk))
        ensure_user_has_permission(request_user, volunteer_skill.user, 'user.is_same_user')
        volunteer_skill.delete()

    @staticmethod
    def user_has_skills(request_user):
        return VolunteerSkill.objects.filter(user=request_user).exists()

    @staticmethod
    def get_user_todos(request_user, user):
        ensure_user_has_permission(request_user, user, 'user.is_same_user')
        todos = []
        if user.initial_type == UserType.VOLUNTEER:
            if not VolunteerProfile.objects.filter(user=user).exists():
                todos.append({'text':'You have not created a volunteer profile yet!'})
            else:
                if not ProjectService.user_is_volunteer(request_user):
                    todos.append({'text':'You are not volunteering for any organization, find a new project.'})
                if not UserService.user_has_skills(request_user):
                    todos.append({'text':'You have no listed skills, edit your profile and add some.'})
        elif user.initial_type == UserType.ORGANIZATION:
            if not OrganizationRole.objects.filter(user=user).exists():
                todos.append({'text':'You are not part of any organization - create or join one!'})

        for org in OrganizationService.get_user_organizations_with_pending_requests(request_user):
            todos.append({'text':'Organization {0} has pending membership request reviews.'.format(org.name)})

        for proj in ProjectService.get_user_projects_with_pending_volunteer_requests(request_user):
            todos.append({'text':'Project {0} has pending volunteer application reviews'.format(proj.name)})

        for proj in ProjectService.get_user_projects_with_pending_task_requests(request_user):
            todos.append({'text':'Project {0} has pending task QA reviews'.format(proj.name)})

        for proj in ProjectService.get_user_projects_in_draft_status(request_user):
            todos.append({'text':'Project {0} is still in draft status and needs to be completed and published.'.format(proj.name)})

        for task in ProjectTaskService.get_user_in_progress_tasks(request_user):
            todos.append({'text':'Task {0} from proj {1} in progress.'.format(task.name, task.project.name)})

        return todos
