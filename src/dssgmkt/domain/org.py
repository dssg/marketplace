from django.db import models, IntegrityError
from django.db.models import Case, Q, When

from ..models.common import OrgRole, ReviewStatus
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole,
)

class OrganizationService():
    @staticmethod
    def get_all_organizations(request_user):
        return Organization.objects.order_by('name')

    @staticmethod
    def user_is_organization_member(user, org):
        return OrganizationRole.objects.filter(organization=org, user=user).exists()

    @staticmethod
    def user_is_organization_staff(user, org):
        return OrganizationRole.objects.filter(organization=org, user=user, role=OrgRole.STAFF).exists()

    @staticmethod
    def user_is_organization_admin(user, org):
        return OrganizationRole.objects.filter(organization=org, user=user, role=OrgRole.ADMINISTRATOR).exists()

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
        else:
            raise KeyError('Organization not found ' + str(orgid))

    @staticmethod
    def save_membership_request(request_user, orgid, membership_request):
        if membership_request.organization.id == orgid:
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

    @staticmethod
    def reject_membership_request(request_user, orgid, membership_request):
        membership_request.status = ReviewStatus.REJECTED
        OrganizationService.save_membership_request(request_user, orgid, membership_request)

    @staticmethod
    def save_organization_role(request_user, orgid, organization_role):
        if organization_role.organization.id == orgid:
            organization_role.save()
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


    @staticmethod
    def delete_organization_role(request_user, orgid, organization_role):
        if organization_role.organization.id != orgid:
            raise ValueError('Role does not match organization')
        else:
            organization_role.delete()
