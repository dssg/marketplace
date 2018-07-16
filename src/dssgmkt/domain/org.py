from django.db import IntegrityError, transaction
from django.db.models import Case, Q, When

from ..models.common import OrgRole, ReviewStatus
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole,
)
from ..models.user import (
    User, NotificationSeverity, NotificationSource,
)
from .notifications import NotificationService
from .proj import ProjectService

from .common import validate_consistent_keys

from dssgmkt.authorization.common import ensure_user_has_permission

class OrganizationService():
    @staticmethod
    def get_all_organizations(request_user):
        return Organization.objects.order_by('name')

    @staticmethod
    def get_organization(request_user, org_pk):
        return Organization.objects.get(pk=org_pk)

    @staticmethod
    def save_organization_info(request_user, orgid, organization):
        ensure_user_has_permission(request_user, organization, 'organization.information_edit')
        validate_consistent_keys(organization, ('id', orgid))
        if organization.id == orgid:
            organization.save()
        else:
            raise ValueError('Request does not match organization')

    @staticmethod
    def create_organization(request_user, organization):
        ensure_user_has_permission(request_user, organization, 'organization.create')
        if Organization.objects.filter(name=organization.name).exists():
            raise ValueError('An organization with this name already exists.')
        with transaction.atomic():
            organization.save()
            admin_role = OrganizationRole()
            admin_role.user = request_user
            admin_role.organization = organization
            admin_role.role = OrgRole.ADMINISTRATOR
            admin_role.save()
            message = "You have created the organization {0} and have been made its administrator user.".format(organization.name)
            NotificationService.add_user_notification(request_user,
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
    def user_is_any_organization_member(user):
        return user.is_authenticated and OrganizationRole.objects.filter(user=user).exists()

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
    def get_organization_projects(request_user, org):
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
    def get_organization_admins(request_user, org):
        return User.objects.filter(organizationrole__role=OrgRole.ADMINISTRATOR, organizationrole__organization=org)

    @staticmethod
    def get_organizations_with_user_create_project_permission(request_user):
        if request_user.is_anonymous:
            return []
        all_user_orgs = Organization.objects.filter(organizationrole__user=request_user)
        orgs = []
        for org in all_user_orgs:
            if request_user.has_perm('organization.project_create', org):
                orgs.append(org)
        return orgs

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
                NotificationService.add_user_notification(organization_role.user,
                                                            "You have been added as a member of " + organization_role.organization.name + " with " + organization_role.get_role_display() + " role.",
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.ORGANIZATION,
                                                            organization_role.organization.id)
            except IntegrityError:
                raise ValueError('Duplicate user role')
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
                    NotificationService.add_user_notification(membership_request.user,
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
        OrganizationService.save_membership_request(request_user, orgid, membership_request)
        NotificationService.add_user_notification(membership_request.user,
                                                    "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
                                                    membership_request.id)

    @staticmethod
    def reject_membership_request(request_user, orgid, membership_request):
        validate_consistent_keys(membership_request, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, membership_request, 'organization.membership_review')
        membership_request.status = ReviewStatus.REJECTED
        OrganizationService.save_membership_request(request_user, orgid, membership_request)
        NotificationService.add_user_notification(membership_request.user,
                                                    "Your membership request for " + membership_request.organization.name + " was rejected.",
                                                    NotificationSeverity.WARNING,
                                                    NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
                                                    membership_request.id)

    @staticmethod
    def save_organization_role(request_user, orgid, organization_role):
        validate_consistent_keys(organization_role, (['organization','id'], orgid))
        ensure_user_has_permission(request_user, organization_role, 'organization.role_edit')
        if organization_role.organization.id == orgid:
            organization_role.save()
            NotificationService.add_user_notification(organization_role.user,
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
            NotificationService.add_user_notification(request_user,
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
        organization_role.delete()
        NotificationService.add_user_notification(organization_role.user,
                                                    "You were removed as a staff member of " + organization_role.organization.name,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.ORGANIZATION,
                                                    organization_role.organization.id)


    @staticmethod
    def get_user_organizations_with_pending_requests(request_user):
        return Organization.objects.filter(organizationrole__user=request_user,
                                            organizationrole__role=OrgRole.ADMINISTRATOR,
                                            organizationmembershiprequest__status=ReviewStatus.NEW).distinct()
