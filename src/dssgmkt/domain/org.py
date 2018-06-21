from django.db import models, IntegrityError
from django.db.models import Case, Q, When

from ..models.common import OrgRole, ReviewStatus
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole,
)

class OrganizationService():
    def get_all_organizations(request_user):
        return Organization.objects.order_by('name')

    def user_is_organization_member(request_user, user, org):
        return OrganizationRole.objects.filter(organization=org, user=user).exists()

    def user_is_organization_staff(request_user, user, org):
        return OrganizationRole.objects.filter(organization=org, user=user, role=OrgRole.STAFF).exists()

    def user_is_organization_admin(request_user, user, org):
        return OrganizationRole.objects.filter(organization=org, user=user, role=OrgRole.ADMINISTRATOR).exists()

    def get_organization_staff(request_user, org):
        return org.organizationrole_set.order_by('role')

    def get_membership_requests(request_user, org):
        return org.organizationmembershiprequest_set.all().order_by(
                Case(When(status=ReviewStatus.NEW, then=0),
                     When(status=ReviewStatus.ACCEPTED, then=1),
                     When(status=ReviewStatus.REJECTED, then=2)), '-request_date')

    # TODO check for permissions (user is admin role of the organization in question)
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
