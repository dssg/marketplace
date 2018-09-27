from rules import add_perm, predicate

from dssgmkt.domain.org import OrganizationService
from dssgmkt.domain.user import UserService

@predicate
def is_organization_creator(user, org=None):
    return user.is_authenticated and UserService.user_is_organization_creator(user)

add_perm('organization.create', is_organization_creator)
add_perm('organization.information_edit', OrganizationService.user_is_organization_admin)
add_perm('organization.staff_view', OrganizationService.user_is_organization_member)
add_perm('organization.staff_edit', OrganizationService.user_is_organization_admin)

@predicate
def is_organization_role_admin(user, organization_role):
    return OrganizationService.user_is_organization_admin(user, organization_role.organization)

@predicate
def is_organization_membership_request_staff(user, membership_request):
    return OrganizationService.user_is_organization_staff(user, membership_request.organization)

@predicate
def is_organization_membership_request_admin(user, membership_request):
    return OrganizationService.user_is_organization_admin(user, membership_request.organization)

@predicate
def is_own_membership(user, organization_role):
    return user == organization_role.user

@predicate
def is_own_membership_request(user, membership_request):
    return user.is_authenticated and user == membership_request.user

add_perm('organization.role_add', is_organization_role_admin)
add_perm('organization.role_edit', is_organization_role_admin)
add_perm('organization.role_delete', is_organization_role_admin)

add_perm('organization.membership_request_view', is_own_membership_request | is_organization_membership_request_staff)
add_perm('organization.membership_review', is_organization_membership_request_admin)
add_perm('organization.membership_leave', is_own_membership)

add_perm('organization.project_create', OrganizationService.user_is_organization_admin)
