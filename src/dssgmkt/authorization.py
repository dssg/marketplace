from rules import predicate, add_perm

@predicate
def is_organization_admin(user, organization):
    return user.is_authenticated and user.is_organization_admin(organization)

@predicate
def is_organization_staff(user, organization):
    return user.is_authenticated and user.is_organization_staff(organization)

@predicate
def is_organization_member(user, organization):
    return user.is_authenticated and user.is_organization_member(organization)

add_perm('organization.information_edit', is_organization_admin)
add_perm('organization.staff_view', is_organization_member)
add_perm('organization.staff_edit', is_organization_admin)

@predicate
def is_organization_role_admin(user, organization_role):
    return is_organization_admin(user, organization_role.organization)

@predicate
def is_organization_membership_request_admin(user, membership_request):
    return is_organization_admin(user, membership_request.organization)

@predicate
def is_own_membership(user, organization_role):
    return user == organization_role.user

add_perm('organization.role_add', is_organization_role_admin)
add_perm('organization.role_edit', is_organization_role_admin)
add_perm('organization.role_delete', is_organization_role_admin)

add_perm('organization.membership_review', is_organization_membership_request_admin)
add_perm('organization.membership_leave', is_own_membership)