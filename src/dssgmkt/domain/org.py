from django.db import models, IntegrityError, transaction
from django.db.models import Case, Q, When

from ..models.common import OrgRole, ReviewStatus
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole,
)
from ..models.user import (
    NotificationSeverity, NotificationSource,
)
from .notifications import NotificationService

class OrganizationService():
    @staticmethod
    def get_all_organizations(request_user):
        return Organization.objects.order_by('name')

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
    def get_organization_staff(request_user, org):
        return org.organizationrole_set.order_by('role')

    @staticmethod
    def get_membership_requests(request_user, org):
        return org.organizationmembershiprequest_set.all().order_by(
                Case(When(status=ReviewStatus.NEW, then=0),
                     When(status=ReviewStatus.ACCEPTED, then=1),
                     When(status=ReviewStatus.REJECTED, then=2)), '-request_date')

    # TODO check for permissions (user is admin role of the organization in question)
    @staticmethod
    def add_staff_member(request_user, orgid, organization_role):
        organization = Organization.objects.get(pk=orgid)
        if organization:
            organization_role.organization = organization
            try:
                organization_role.save()
                NotificationService.add_user_notification(organization_role.user,
                                                            "You have been added as a member of " + organization_role.organization.name + " with " + organization_role.get_role_display() + " role.",
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.ORGANIZATION)
            except IntegrityError:
                raise ValueError('Duplicate user role')
        else:
            raise KeyError('Organization not found ' + str(orgid))

    @staticmethod
    def create_membership_request(request_user, user, orgid, membership_request):
        organization = Organization.objects.get(pk=orgid)
        if organization:
            membership_request.organization = organization
            membership_request.user = user
            membership_request.status = ReviewStatus.NEW
            membership_request.role = OrgRole.STAFF
            # try:
            membership_request.save()
            # except IntegrityError:
            #     raise ValueError('Duplicate user role')
            NotificationService.add_user_notification(membership_request.user,
                                                        "You have applied to be a member of " + membership_request.organization.name  + " with " + membership_request.get_role_display() + " role. You will be notified when the organization's administrators review your membership request.",
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST)
        else:
            raise KeyError('Organization not found ' + str(orgid))

    @staticmethod
    def save_membership_request(request_user, orgid, membership_request):
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
        membership_request.status = ReviewStatus.ACCEPTED
        OrganizationService.save_membership_request(request_user, orgid, membership_request)
        NotificationService.add_user_notification(membership_request.user,
                                                    "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST)

    @staticmethod
    def reject_membership_request(request_user, orgid, membership_request):
        membership_request.status = ReviewStatus.REJECTED
        OrganizationService.save_membership_request(request_user, orgid, membership_request)
        NotificationService.add_user_notification(membership_request.user,
                                                    "Your membership request for " + membership_request.organization.name + " was rejected.",
                                                    NotificationSeverity.WARNING,
                                                    NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST)

    @staticmethod
    def save_organization_role(request_user, orgid, organization_role):
        if organization_role.organization.id == orgid:
            organization_role.save()
            NotificationService.add_user_notification(organization_role.user,
                                                        "Your role within " + organization_role.organization.name + " has been changed to " + organization_role.get_role_display() + ".",
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION)
        else:
            raise ValueError('Role does not match organization')

    @staticmethod
    def leave_organization(request_user, orgid, organization_role):
        if organization_role.organization.id != orgid:
            raise ValueError('Role does not match organization')
        elif organization_role.user != request_user:
            raise ValueError('Role does not match current user')
        else:
            organization_role.delete()
            NotificationService.add_user_notification(request_user,
                                                        "You left " + organization_role.organization.name,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION)


    @staticmethod
    def delete_organization_role(request_user, orgid, organization_role):
        if organization_role.organization.id != orgid:
            raise ValueError('Role does not match organization')
        else:
            organization_role.delete()
            NotificationService.add_user_notification(organization_role.user,
                                                        "You were removed as a staff member of " + organization_role.organization.name,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.ORGANIZATION)
