from django.db import IntegrityError, transaction
from django.db.models import Q, Count

from ..models.common import (
    ReviewStatus, SkillLevel,
)
from ..models.user import (
    User, UserType, VolunteerProfile, VolunteerSkill, UserBadge, BadgeType, BadgeTier, Skill,
    NotificationSource, NotificationSeverity, SignupCode, SignupCodeType,
)
from ..models.org import (
    OrganizationRole,
)

from .common import validate_consistent_keys, award_view_model_translation
from .org import OrganizationService
from .proj import ProjectService, ProjectTaskService
from .notifications import NotificationService

from dssgmkt.authorization.common import ensure_user_has_permission

class UserService():
    @staticmethod
    def get_user(request_user, userid):
        return User.objects.get(pk=userid)

    @staticmethod
    def get_all_volunteer_profiles(request_user, search_config=None):
        base_query = VolunteerProfile.objects.filter(volunteer_status=ReviewStatus.ACCEPTED)
        if search_config:
            if 'username' in search_config:
                for name_fragment in search_config['username'].split():
                    base_query = base_query.filter(Q(user__first_name__icontains=name_fragment) | \
                                                   Q(user__last_name__icontains=name_fragment) | \
                                                   Q(user__username__icontains=name_fragment))
            if 'skills' in search_config:
                for skill_fragment in search_config['skills'].split():
                    base_query = base_query.filter(user__volunteerskill__skill__name__icontains=skill_fragment.strip())
            if 'awards' in search_config:
                aw = search_config['awards']
                if isinstance(aw, str):
                    aw = [aw]
                awards = []
                for award_from_view in aw:
                    awards.append(award_view_model_translation[award_from_view])
                base_query = base_query.filter(user__userbadge__type__in=awards)
            # if 'project_status' in search_config:
            #     project_status_list = search_config['project_status']
            #     if isinstance(project_status_list, str):
            #         project_status_list = [project_status_list]
            #     project_statuses = []
            #     for project_status_from_view in project_status_list:
            #         project_statuses.append(project_status_view_model_translation[project_status_from_view])
            #     base_query = base_query.filter(status__in=project_statuses).distinct()
        return base_query.distinct().order_by('user__first_name', 'user__last_name')


    @staticmethod
    def user_is_dssg_staff(request_user, user):
        print(request_user, user)
        return user.is_authenticated and user.initial_type == UserType.DSSG_STAFF

    @staticmethod
    def get_featured_volunteer():
        return VolunteerProfile.objects.all().annotate(taskcount=Count('user__projecttaskrole')).order_by('-average_review_score', '-taskcount')[0]

    @staticmethod
    def create_user(request_user, new_user, user_type):
        with transaction.atomic():
            if not user_type in ['volunteer', 'organization']:
                raise ValueError('Unknown user type')
            if user_type == 'volunteer':
                new_user.initial_type = UserType.VOLUNTEER
            elif user_type == 'organization':
                new_user.initial_type = UserType.ORGANIZATION
            new_user.save()

            if new_user.initial_type == UserType.VOLUNTEER:
                UserService.create_volunteer_profile(new_user, new_user.id)
            return new_user


    @staticmethod
    def save_user(request_user, user_pk, user):
        validate_consistent_keys(user, ('id', user_pk))
        user.save()


    @staticmethod
    def get_signup_code_type_by_text(code):
        if code:
            existing_signup_codes = SignupCode.objects.filter(name=code).values('type')
            return [code.get('type') for code in existing_signup_codes]
        else:
            return None

    @staticmethod
    def verify_if_automatically_approved(volunteer_profile):
        signup_code = volunteer_profile.user.special_code
        existing_code_types = UserService.get_signup_code_type_by_text(signup_code)
        if existing_code_types and SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT in existing_code_types:
            volunteer_profile.volunteer_status = ReviewStatus.ACCEPTED
            volunteer_profile.is_edited = True
        else:
            volunteer_profile.volunteer_status = ReviewStatus.NEW
            volunteer_profile.is_edited = False


    @staticmethod
    def create_volunteer_profile(request_user, user_pk):
        target_user = UserService.get_user(request_user, user_pk)
        ensure_user_has_permission(request_user, target_user, 'user.is_same_user')
        if not VolunteerProfile.objects.filter(user=request_user).exists():
            volunteer_profile = VolunteerProfile()
            volunteer_profile.user = request_user
            UserService.verify_if_automatically_approved(volunteer_profile)
            try:
                volunteer_profile.save()

                new_badge_tier = None
                if volunteer_profile.id < 100:
                    new_badge_tier = BadgeTier.MASTER
                elif volunteer_profile.id < 500:
                    new_badge_tier = BadgeTier.ADVANCED
                elif volunteer_profile.id < 1000:
                    new_badge_tier = BadgeTier.BASIC
                if new_badge_tier is not None:
                    new_user_badge = UserBadge()
                    new_user_badge.tier = new_badge_tier
                    new_user_badge.type = BadgeType.EARLY_USER
                    new_user_badge.user = volunteer_profile.user
                    new_user_badge.save()

                return volunteer_profile
            except IntegrityError:
                raise ValueError('User already has a volunteer profile')


    @staticmethod
    def save_volunteer_profile(request_user, volunteer_pk, volunteer_profile):
        validate_consistent_keys(volunteer_profile, ('id', volunteer_pk))
        ensure_user_has_permission(request_user, volunteer_profile.user, 'user.is_same_user')
        volunteer_profile.is_edited = True
        volunteer_profile.save()

    @staticmethod
    def accept_volunteer_profile(request_user, volunteer_pk):
        ensure_user_has_permission(request_user, request_user, 'volunteer.new_user_review')
        volunteer_profile = VolunteerProfile.objects.get(pk=volunteer_pk)
        if volunteer_profile:
            volunteer_profile.volunteer_status = ReviewStatus.ACCEPTED
            volunteer_profile.is_edited = True
            volunteer_profile.save()
            NotificationService.add_user_notification(volunteer_profile.user,
                    "Congratulations! you have been accepted as a volunteer and can now apply to work on open projects.",
                    NotificationSeverity.INFO,
                    NotificationSource.VOLUNTEER_APPLICATION,
                    volunteer_profile.id)
        else:
            raise KeyError("Volunteer profile not found.")

    @staticmethod
    def reject_volunteer_profile(request_user, volunteer_pk):
        ensure_user_has_permission(request_user, request_user, 'volunteer.new_user_review')
        volunteer_profile = VolunteerProfile.objects.get(pk=volunteer_pk)
        if volunteer_profile:
            volunteer_profile.volunteer_status = ReviewStatus.REJECTED
            volunteer_profile.is_edited = True
            volunteer_profile.save()
            NotificationService.add_user_notification(volunteer_profile.user,
                    "Unfortunately your volunteer application was not approved at the time.",
                    NotificationSeverity.INFO,
                    NotificationSource.VOLUNTEER_APPLICATION,
                    volunteer_profile.id)
        else:
            raise KeyError("Volunteer profile not found.")

    @staticmethod
    def get_skill_levels():
        return SkillLevel.get_choices()

    @staticmethod
    def get_volunteer_skills(request_user, user_pk):
        volunteer_skill_list = VolunteerSkill.objects.filter(user__id=user_pk)
        volunteer_skill_dict = {}
        for skill in volunteer_skill_list:
            volunteer_skill_dict[skill.skill.id] = skill

        all_skills = Skill.objects.all()
        all_areas = Skill.objects.values('area').distinct()
        result_skills = {}
        for row in all_areas:
            result_skills[row['area']] = []
        for skill in all_skills:
            result_skills[skill.area].append({'system_skill': skill, 'volunteer_skill': volunteer_skill_dict.get(skill.id)})
        return result_skills

    @staticmethod
    def set_volunteer_skills(request_user, user_pk, post_object):
        target_user = UserService.get_user(request_user, user_pk)
        ensure_user_has_permission(request_user, target_user, 'user.is_same_user')
        volunteer_skill_list = VolunteerSkill.objects.filter(user__id=user_pk)
        volunteer_skill_dict = {}
        for skill in volunteer_skill_list:
            volunteer_skill_dict[skill.skill.id] = skill

        all_skills = Skill.objects.all()
        for skill in all_skills:
            form_value = int(post_object.get(str(skill.id)))
            volunteer_value = volunteer_skill_dict.get(skill.id)
            if form_value == -1:
                if volunteer_value:
                    volunteer_value.delete()
            else:
                if volunteer_value:
                    volunteer_value.level = form_value
                else:
                    volunteer_value = VolunteerSkill()
                    volunteer_value.skill = skill
                    volunteer_value.level = form_value
                    volunteer_value.user = target_user
                volunteer_value.save()

    @staticmethod
    def user_has_skills(request_user):
        return VolunteerSkill.objects.filter(user=request_user).exists()

    @staticmethod
    def user_has_volunteer_profile(request_user):
        return VolunteerProfile.objects.filter(user=request_user).exists()

    @staticmethod
    def user_has_approved_volunteer_profile(request_user):
        return VolunteerProfile.objects.filter(user=request_user, volunteer_status=ReviewStatus.ACCEPTED).exists()

    @staticmethod
    def user_is_organization_creator(request_user):
        return request_user.is_authenticated and request_user.initial_type == UserType.ORGANIZATION

    @staticmethod
    def get_pending_volunteer_profiles(request_user):
        ensure_user_has_permission(request_user, request_user, 'volunteer.new_user_review')
        return VolunteerProfile.objects.filter(volunteer_status=ReviewStatus.NEW).order_by('is_edited', '-creation_date')


    @staticmethod
    def get_user_todos(request_user, user):
        ensure_user_has_permission(request_user, user, 'user.is_same_user')
        todos = []
        if user.initial_type == UserType.VOLUNTEER:
            if not UserService.user_has_volunteer_profile(request_user):
                todos.append({'text':'You have not created a volunteer profile yet!'})
            else:
                if not request_user.volunteerprofile.is_edited:
                    todos.append({'text':'You should fill out your volunteer profile.'})
                elif not ProjectService.user_is_volunteer(request_user) and request_user.volunteerprofile.is_accepted:
                    todos.append({'text':'You are not volunteering for any organization, find a new project.'})
                if not UserService.user_has_skills(request_user):
                    todos.append({'text':'You have no listed skills, your should add your expertise to your profile.'})
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

        return todos

    @staticmethod
    def get_volunteer_leaderboards(request_user):
        return [{'title': 'Best reviewed',
                 'data': User.objects.order_by('-volunteerprofile__average_review_score')[0:10],
                 'type': 'review',
                 'badge': UserBadge(type=BadgeType.REVIEW_SCORE, tier=BadgeTier.MASTER),
                },
                {'title': 'Most completed projects',
                 'data': User.objects.order_by('-volunteerprofile__completed_task_count')[0:10],
                 'type': 'review',
                 'badge':  UserBadge(type=BadgeType.NUMBER_OF_PROJECTS, tier=BadgeTier.MASTER),
                },
                {'title': 'Meets deadlines',
                 'data': User.objects.order_by('-volunteerprofile__ahead_of_time_task_ratio')[0:10],
                 'type': 'review',
                 'badge': UserBadge(type=BadgeType.WORK_SPEED, tier=BadgeTier.MASTER),
                }, ]
