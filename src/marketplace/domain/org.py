from itertools import accumulate

from django.db import IntegrityError, transaction
from django.db.models import Case, Q, When, Count

from ..models.common import OrgRole, ReviewStatus, SocialCause
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole, OrganizationSocialCause, OrganizationType,
)
from ..models.user import (
    User, NotificationSeverity, NotificationSource,
)
from ..models.proj import ProjectStatus
from .notifications import NotificationDomain, NotificationService
from .proj import ProjectService

from .common import validate_consistent_keys, social_cause_view_model_translation, project_status_view_model_translation, org_type_view_model_translation

from marketplace.authorization.common import ensure_user_has_permission


class OrganizationService():
    @staticmethod
    def get_all_organizations(request_user, search_config=None):
        base_query = Organization.objects.all()
        if search_config:
            if 'name' in search_config:
                base_query = base_query.filter(name__icontains=search_config['name'])
            if 'social_cause' in search_config:
                sc = search_config['social_cause']
                if isinstance(sc, str):
                    sc = [sc]
                social_causes = []
                for social_cause_from_view in sc:
                    social_causes.append(social_cause_view_model_translation[social_cause_from_view])
                base_query = base_query.filter(organizationsocialcause__social_cause__in=social_causes).distinct()
            if 'type' in search_config:
                sc = search_config['type']
                if isinstance(sc, str):
                    sc = [sc]
                types = []
                for type_from_view in sc:
                    types.append(org_type_view_model_translation[type_from_view])
                base_query = base_query.filter(type__in=types).distinct()
            if 'project_status' in search_config:
                project_status_list = search_config['project_status']
                if isinstance(project_status_list, str):
                    project_status_list = [project_status_list]
                project_statuses = []
                for project_status_from_view in project_status_list:
                    project_statuses.append(project_status_view_model_translation[project_status_from_view])
                base_query = base_query.filter(project__status__in=project_statuses).distinct()
        return base_query.order_by('name')

    @staticmethod
    def get_organization(request_user, org_pk):
        return Organization.objects.get(pk=org_pk)

    @staticmethod
    def get_featured_organization():
        # Long-term, devise a better way of selecting a featured organization.
        return Organization.objects.filter(type=OrganizationType.SOCIAL_GOOD) \
                                .annotate(projectcount=Count('project')) \
                                .order_by('-projectcount').first()


    @staticmethod
    def save_organization_info(request_user, orgid, organization):
        ensure_user_has_permission(request_user, organization, 'organization.information_edit')
        validate_consistent_keys(organization, ('id', orgid))
        if organization.id == orgid:
            organization.save()
        else:
            raise ValueError('Request does not match organization')

    @staticmethod
    def save_organization_social_causes(request_user, orgid, organization, post_object):
        ensure_user_has_permission(request_user, organization, 'organization.information_edit')
        validate_consistent_keys(organization, ('id', orgid))
        social_causes = post_object.getlist('id_social_causes')
        with transaction.atomic():
            for sc in OrganizationSocialCause.objects.filter(organization=orgid):
                sc.delete()
            for sc in social_causes:
                new_sc = OrganizationSocialCause()
                new_sc.social_cause = sc
                new_sc.organization = organization
                new_sc.save()

    @staticmethod
    def create_organization(request_user, organization, org_type='socialgood'):
        ensure_user_has_permission(request_user, org_type, 'organization.create')
        if Organization.objects.filter(name=organization.name).exists():
            raise ValueError('An organization with this name already exists.')
        with transaction.atomic():
            organization.type = org_type_view_model_translation[org_type]
            if organization.type is None:
                organization.type = OrganizationType.SOCIAL_GOOD
            organization.save()
            admin_role = OrganizationRole()
            admin_role.user = request_user
            admin_role.organization = organization
            admin_role.role = OrgRole.ADMINISTRATOR
            admin_role.save()
            message = "You have created the organization {0} and have been made its administrator user.".format(organization.name)
            NotificationDomain.add_user_notification(request_user,
                                                        message,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION,
                                                        organization.id)
            return organization

    @staticmethod
    def get_organization_membership_request(request_user, org_pk, request_pk):
        return OrganizationMembershipRequest.objects.get(pk=request_pk, organization=org_pk)

    @staticmethod
    def get_organization_role(request_user, org_pk, user_pk):
        return OrganizationRole.objects.get(organization=org_pk, user=user_pk)

    @staticmethod
    def get_organization_role_by_pk(request_user, org_pk, role_pk):
        return OrganizationRole.objects.get(organization=org_pk, pk=role_pk)

    @staticmethod
    def user_is_any_organization_member(user):
        return user.is_authenticated and OrganizationRole.objects.filter(user=user, organization__type=OrganizationType.SOCIAL_GOOD).exists()

    @staticmethod
    def user_is_organization_member(user, org):
        return user.is_authenticated and OrganizationRole.objects.filter(organization=org, user=user).exists()

    @staticmethod
    def user_is_organization_staff(user, org):
        return user.is_authenticated and OrganizationRole.objects.filter(organization=org, user=user, role=OrgRole.STAFF).exists()

    @staticmethod
    def user_is_organization_admin(user, org):
        return user.is_authenticated and OrganizationRole.objects.filter(organization=org, user=user, role=OrgRole.ADMINISTRATOR).exists()

    @staticmethod
    def user_is_pending_membership(user, org):
        return user.is_authenticated and OrganizationMembershipRequest.objects.filter(organization=org, user=user, status=ReviewStatus.NEW).exists()

    @staticmethod
    def get_organization_staff(request_user, org):
        return org.organizationrole_set.order_by('role')

    @staticmethod
    def get_organization_members(request_user, org):
        return User.objects.filter(organizationrole__organization=org)

    @staticmethod
    def get_organization_admins(request_user, org):
        return User.objects.filter(organizationrole__role=OrgRole.ADMINISTRATOR, organizationrole__organization=org)

    @staticmethod
    def get_all_users_not_organization_members(orgid, query=None):
        base_query = User.objects.exclude(organizationrole__organization__id=orgid)
        if query:
            base_query = base_query.filter(Q(first_name__icontains=query) | \
                                              Q(last_name__icontains=query) | \
                                              Q(email__icontains=query) | \
                                              Q(username__icontains=query))
        return base_query.values('first_name', 'last_name', 'username', 'id').order_by('first_name', 'last_name')[:25]

    @staticmethod
    def get_organization_projects(request_user, org):
        if org.is_volunteer_group():
            return ProjectService.get_all_organization_member_volunteer_projects(request_user, org)
        else:
            if OrganizationService.user_is_organization_member(request_user, org):
                return ProjectService.get_all_organization_projects(request_user, org)
            else:
                return ProjectService.get_organization_public_projects(request_user, org)

    @staticmethod
    def create_project(request_user, orgid, project):
        organization = OrganizationService.get_organization(request_user, orgid)
        organization_members = OrganizationService.get_organization_members(request_user, orgid)
        return ProjectService.create_project(request_user, project, organization, organization_members)


    @staticmethod
    def get_organizations_with_user_create_project_permission(request_user):
        if request_user.is_anonymous:
            return []
        all_user_orgs = Organization.objects.filter(organizationrole__user=request_user, type=OrganizationType.SOCIAL_GOOD)
        orgs = []
        for org in all_user_orgs:
            if request_user.has_perm('organization.project_create', org):
                orgs.append(org)
        return orgs

    @staticmethod
    def user_can_create_projects(request_user):
        if request_user.is_anonymous:
            return False
        all_user_orgs = Organization.objects.filter(organizationrole__user=request_user, type=OrganizationType.SOCIAL_GOOD)
        for org in all_user_orgs:
            if request_user.has_perm('organization.project_create', org):
                return True
        return False

    @staticmethod
    def get_membership_requests(request_user, org):
        ensure_user_has_permission(request_user, org, 'organization.staff_view')
        return org.organizationmembershiprequest_set.all().order_by(
                Case(When(status=ReviewStatus.NEW, then=0),
                     When(status=ReviewStatus.ACCEPTED, then=1),
                     When(status=ReviewStatus.REJECTED, then=1)), '-request_date')

    @staticmethod
    def add_staff_member(request_user, orgid, organization_role):
        organization = Organization.objects.get(pk=orgid)
        if organization:
            ensure_user_has_permission(request_user, organization, 'organization.staff_edit')
            organization_role.organization = organization
            try:
                organization_role.save()
                NotificationDomain.add_user_notification(organization_role.user,
                                                            "You have been added as a member of " + organization_role.organization.name + " with " + organization_role.get_role_display() + " role.",
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.ORGANIZATION,
                                                            organization_role.organization.id)
            except IntegrityError:
                raise ValueError('Duplicate user role')
        else:
            raise KeyError('Organization not found ' + str(orgid))

    @staticmethod
    def add_staff_member_by_id(request_user, orgid, userid, role):
        organization = Organization.objects.get(pk=orgid)
        user = User.objects.get(pk=userid)
        if organization and user:
            # We delegate the permissions check to add_staff_member
            # ensure_user_has_permission(request_user, organization, 'organization.staff_edit')
            organization_role = OrganizationRole()
            organization_role.organization = organization
            organization_role.user = user
            if role:
                organization_role.role = role
            else:
                organization_role.role = OrgRole.STAFF
            OrganizationService.add_staff_member(request_user, orgid, organization_role)
        else:
            raise KeyError('Organization not found ' + str(orgid))

    @staticmethod
    def create_membership_request(request_user, user, orgid, membership_request):
        organization = Organization.objects.get(pk=orgid)
        if organization:
            if not OrganizationService.user_is_organization_member(user, organization):
                membership_request.organization = organization
                membership_request.user = user
                membership_request.status = ReviewStatus.NEW
                membership_request.role = OrgRole.STAFF
                if not OrganizationService.user_is_pending_membership(user, organization):
                    membership_request.save()
                    NotificationDomain.add_user_notification(membership_request.user,
                                                                "You have applied to be a member of " + membership_request.organization.name + ". You will be notified when the organization's administrators review your membership request.",
                                                                NotificationSeverity.INFO,
                                                                NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
                                                                membership_request.id)
            else:
                raise KeyError('User is already a member of the organization ' + str(orgid))
        else:
            raise KeyError('Organization not found ' + str(orgid))

    @staticmethod
    def save_membership_request(request_user, orgid, membership_request):
        validate_consistent_keys(membership_request, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, membership_request, 'organization.membership_review')
        if membership_request.organization.id == orgid:
            with transaction.atomic():
                membership_request.save()
                if membership_request.status == ReviewStatus.ACCEPTED and not OrganizationService.user_is_organization_member(membership_request.user, membership_request.organization):
                    new_role = OrganizationRole(role = membership_request.role, user = membership_request.user, organization = membership_request.organization)
                    new_role.save()
        else:
            raise ValueError('Membership request does not match organization')

    @staticmethod
    def accept_membership_request(request_user, orgid, membership_request):
        validate_consistent_keys(membership_request, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, membership_request, 'organization.membership_review')
        membership_request.status = ReviewStatus.ACCEPTED
        membership_request.reviewer = request_user
        OrganizationService.save_membership_request(request_user, orgid, membership_request)
        NotificationDomain.add_user_notification(membership_request.user,
                                                    "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
                                                    membership_request.id)

    @staticmethod
    def reject_membership_request(request_user, orgid, membership_request):
        validate_consistent_keys(membership_request, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, membership_request, 'organization.membership_review')
        membership_request.status = ReviewStatus.REJECTED
        membership_request.reviewer = request_user
        OrganizationService.save_membership_request(request_user, orgid, membership_request)
        NotificationDomain.add_user_notification(membership_request.user,
                                                    "Your membership request for " + membership_request.organization.name + " was rejected.",
                                                    NotificationSeverity.WARNING,
                                                    NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
                                                    membership_request.id)

    @staticmethod
    def save_organization_role(request_user, orgid, organization_role):
        validate_consistent_keys(organization_role, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, organization_role, 'organization.role_edit')
        if organization_role.organization.id == orgid:
            current_role = OrganizationService.get_organization_role_by_pk(organization_role.user, orgid, organization_role.id)
            if current_role.role == OrgRole.ADMINISTRATOR and \
                organization_role.role != OrgRole.ADMINISTRATOR and \
                len(OrganizationService.get_organization_admins(request_user, orgid)) <= 1:
                raise ValueError('You are trying to remove the last administrator of the organization. Please appoint another administrator before removing the current one.')
            organization_role.save()
            NotificationDomain.add_user_notification(organization_role.user,
                                                        "Your role within " + organization_role.organization.name + " has been changed to " + organization_role.get_role_display() + ".",
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION,
                                                        organization_role.organization.id)
        else:
            raise ValueError('Role does not match organization')

    @staticmethod
    def leave_organization(request_user, orgid, organization_role):
        validate_consistent_keys(organization_role, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, organization_role, 'organization.membership_leave')
        if organization_role.user != request_user:
            raise ValueError('Role does not match current user')
        else:
            organization_role.delete()
            NotificationDomain.add_user_notification(request_user,
                                                        "You left " + organization_role.organization.name,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION,
                                                        organization_role.organization.id)
            admins = OrganizationService.get_organization_admins(request_user, organization_role.organization)
            NotificationService.add_multiuser_notification(admins,
                                                        organization_role.user.first_name + " " + organization_role.user.last_name + " left " + organization_role.organization.name,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION,
                                                        organization_role.organization.id)


    @staticmethod
    def delete_organization_role(request_user, orgid, organization_role):
        validate_consistent_keys(organization_role, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, organization_role, 'organization.role_delete')
        if organization_role.role == OrgRole.ADMINISTRATOR and len(OrganizationService.get_organization_admins(request_user, orgid)) <= 1:
            raise ValueError('You are trying to remove the last administrator of the organization. Please appoint another administrator before removing the current one.')
        organization_role.delete()
        NotificationDomain.add_user_notification(organization_role.user,
                                                    "You were removed as a staff member of " + organization_role.organization.name,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.ORGANIZATION,
                                                    organization_role.organization.id)


    @staticmethod
    def get_user_organizations_with_pending_requests(request_user):
        return Organization.objects.filter(organizationrole__user=request_user,
                                            organizationrole__role=OrgRole.ADMINISTRATOR,
                                            organizationmembershiprequest__status=ReviewStatus.NEW).distinct()

    @staticmethod
    def get_organization_roles():
        # Reverse this list so the administrator role is not the first one
        return reversed(OrgRole.get_choices())
