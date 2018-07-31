from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from dssgmkt.models.common import ReviewStatus
from dssgmkt.models.user import User, UserType
from dssgmkt.domain.user import UserService

class UserTestCase(TestCase):
    organization_user = None
    dssg_staff_user = None
    volunteer_user = None

    def setUp(self):
        self.organization_user = User()
        self.organization_user.username = "OrgUser"
        self.organization_user.first_name = "Organization"
        self.organization_user.last_name = "User"
        UserService.create_user(None, self.organization_user, 'organization', None)

        self.dssg_staff_user = User()
        self.dssg_staff_user.username = "DSSGStaff"
        self.dssg_staff_user.first_name = "Staff"
        self.dssg_staff_user.last_name = "DSSG"
        UserService.create_user(None, self.staff_user, 'organization', None)
        self.dssg_staff_user.initial_type = UserType.DSSG_STAFF
        UserService.save_user(self.dssg_staff_user, self.dssg_staff_user.id, self.dssg_staff_user)

        self.volunteer_user = User()
        self.volunteer_user.username = "VolUser"
        self.volunteer_user.first_name = "Volunteer"
        self.volunteer_user.last_name = "User"
        self.volunteer_user.email = "volunteer@email.com"
        UserService.create_user(None, self.volunteer_user, 'volunteer', None)
    # 
    # def test_create_organization(self):
    #     all_organizations = OrganizationService.get_all_organizations(self.organization_user)
    #     self.assertFalse(all_organizations.exists())
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.create_organization(AnonymousUser(), self.organization)
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.create_organization(self.volunteer_user, self.organization)
    #
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     all_organizations = OrganizationService.get_all_organizations(self.organization_user)
    #     saved_organization = OrganizationService.get_organization(self.organization_user, self.organization.id)
    #     self.assertEqual(len(all_organizations), 1)
    #     self.assertEqual(all_organizations.first().name, self.organization.name)
    #     self.assertEqual(all_organizations.first(), saved_organization)
    #     self.assertEqual(
    #         list(OrganizationService.get_all_organizations(AnonymousUser())),
    #         list(OrganizationService.get_all_organizations(self.organization_user)),
    #     )
    #     self.assertEqual(
    #         saved_organization,
    #         OrganizationService.get_organization(AnonymousUser(), self.organization.id),
    #     )
    #
    # def test_get_featured_organization(self):
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     self.assertEqual(OrganizationService.get_featured_organization(), self.organization)
    #
    # def test_edit_organization(self):
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     self.organization.name = "EDITED Organization A"
    #     self.organization.short_summary = "EDITED A short description of the org"
    #     self.organization.description = "EDITED A long form description of the organization"
    #     self.organization.website_url = "http://exampleorg.com/EDITED"
    #     self.organization.phone_number = "(111)111-EDITED"
    #     self.organization.email_address = "EDITEDemail@org.org"
    #     self.organization.street_address = "EDITED 1 One Street"
    #     self.organization.city = "EDITED OrgCity"
    #     self.organization.state = "EDITED OrgState"
    #     self.organization.zipcode = "EDITED11111"
    #     self.organization.budget = Budget.B50MP
    #     self.organization.years_operation = YearsInOperation.Y25
    #     self.organization.main_cause = SocialCause.HEALTH
    #     self.organization.organization_scope = GeographicalScope.COUNTRY
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.save_organization_info(AnonymousUser(), self.organization.id, self.organization)
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.save_organization_info(self.volunteer_user, self.organization.id, self.organization)
    #
    #     OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.save_organization_info(self.staff_user, self.organization.id, self.organization)
    #
    #     OrganizationService.save_organization_info(self.organization_user, self.organization.id, self.organization)
    #     self.assertEqual(self.organization, OrganizationService.get_organization(self.organization_user, self.organization.id))
    #
    #
    # def test_filter_organization(self):
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     org_result_list = [self.organization]
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'name': 'ORGAN'})), org_result_list)
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'name': 'no match'})), [])
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'name': ' A'})), org_result_list)
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'social_cause': 'education'})), org_result_list)
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'social_cause': ['education', 'health']})), org_result_list)
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'social_cause': ['health']})), [])
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'project_status': 'new'})), [])
    #     self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'project_status': ['new', 'completed']})), [])
    #
    # def test_create_duplicate_organization(self):
    #     with self.assertRaisesMessage(ValueError, 'An organization with this name already exists.'):
    #         OrganizationService.create_organization(self.organization_user, self.organization)
    #         OrganizationService.create_organization(self.organization_user, self.organization)
    #
    # def test_organization_roles(self):
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     self.assertTrue(OrganizationService.user_is_organization_admin(self.organization_user, self.organization))
    #     self.assertTrue(OrganizationService.user_is_organization_member(self.organization_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_organization_staff(self.organization_user, self.organization))
    #     self.assertTrue(OrganizationService.user_is_any_organization_member(self.organization_user))
    #
    #     self.assertFalse(OrganizationService.user_is_organization_admin(self.volunteer_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_organization_member(self.volunteer_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_organization_staff(self.volunteer_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_any_organization_member(self.volunteer_user))
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.add_staff_member_by_id(AnonymousUser(), self.organization.id, self.staff_user.id, None)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.add_staff_member_by_id(self.staff_user, self.organization.id, self.staff_user.id, None)
    #     OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)
    #
    #     self.assertFalse(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
    #     self.assertTrue(OrganizationService.user_is_organization_member(self.staff_user, self.organization))
    #     self.assertTrue(OrganizationService.user_is_organization_staff(self.staff_user, self.organization))
    #     self.assertTrue(OrganizationService.user_is_any_organization_member(self.staff_user))
    #
    #     organization_staff_roles = OrganizationService.get_organization_staff(self.organization_user, self.organization)
    #     org_admin_user_role = OrganizationService.get_organization_role(self.organization_user, self.organization.id, self.organization_user.id)
    #     org_staff_user_role = OrganizationService.get_organization_role(self.organization_user, self.organization.id, self.staff_user.id)
    #     self.assertEqual(list(organization_staff_roles), [
    #         org_admin_user_role,
    #         org_staff_user_role,
    #     ])
    #     self.assertEqual(org_admin_user_role, OrganizationService.get_organization_role_by_pk(self.organization_user, self.organization.id, org_admin_user_role.id))
    #     self.assertEqual(org_staff_user_role, OrganizationService.get_organization_role_by_pk(self.organization_user, self.organization.id, org_staff_user_role.id))
    #
    #     organization_members = OrganizationService.get_organization_members(self.organization_user, self.organization)
    #     self.assertEqual(set(organization_members), set([self.organization_user, self.staff_user]))
    #
    #     organization_admins = OrganizationService.get_organization_admins(self.organization_user, self.organization)
    #     self.assertEqual(set(organization_admins), set([self.organization_user]))
    #
    #     volunteer_user_match = {
    #         'id': self.volunteer_user.id,
    #         'first_name': self.volunteer_user.first_name,
    #         'last_name': self.volunteer_user.last_name,
    #         'username': self.volunteer_user.username,
    #     }
    #     self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id)), [volunteer_user_match])
    #     self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "olu")), [volunteer_user_match])
    #     self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "volunteer")), [volunteer_user_match])
    #     self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "use")), [volunteer_user_match])
    #     self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "eer@ema")), [volunteer_user_match])
    #     self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "bad_match")), [])
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.leave_organization(AnonymousUser(), self.organization.id, org_staff_user_role)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.leave_organization(self.volunteer_user, self.organization.id, org_staff_user_role)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.leave_organization(self.organization_user, self.organization.id, org_staff_user_role)
    #     OrganizationService.leave_organization(self.staff_user, self.organization.id, org_staff_user_role)
    #     self.assertFalse(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_organization_member(self.staff_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_organization_staff(self.staff_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_any_organization_member(self.staff_user))
    #     with self.assertRaisesMessage(OrganizationRole.DoesNotExist, 'OrganizationRole matching query does not exist.'):
    #         OrganizationService.get_organization_role(self.organization_user, self.organization.id, self.staff_user.id)
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.add_staff_member(AnonymousUser(), self.organization.id, org_staff_user_role)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.add_staff_member(self.staff_user, self.organization.id, org_staff_user_role)
    #     OrganizationService.add_staff_member(self.organization_user, self.organization.id, org_staff_user_role)
    #     org_staff_user_role.role = OrgRole.ADMINISTRATOR
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.save_organization_role(AnonymousUser(), self.organization.id, org_staff_user_role)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.save_organization_role(self.volunteer_user, self.organization.id, org_staff_user_role)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.save_organization_role(self.staff_user, self.organization.id, org_staff_user_role)
    #     OrganizationService.save_organization_role(self.organization_user, self.organization.id, org_staff_user_role)
    #     self.assertTrue(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.delete_organization_role(AnonymousUser(), self.organization.id, org_staff_user_role)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.delete_organization_role(self.volunteer_user, self.organization.id, org_staff_user_role)
    #     OrganizationService.delete_organization_role(self.organization_user, self.organization.id, org_staff_user_role)
    #     self.assertFalse(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
    #     self.assertFalse(OrganizationService.user_is_organization_member(self.staff_user, self.organization))
    #
    # def test_create_duplicate_role(self):
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)
    #     with self.assertRaisesMessage(ValueError, ''):
    #         OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)
    #
    # def test_organization_membership_requests(self):
    #     OrganizationService.create_organization(self.organization_user, self.organization)
    #     self.assertEqual(list(OrganizationService.get_membership_requests(self.organization_user, self.organization)), [])
    #     self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [])
    #
    #     membership_request = OrganizationMembershipRequest()
    #     membership_request.user = self.staff_user
    #     membership_request.role = OrgRole.STAFF
    #     with self.assertRaisesMessage(ValueError, ''):
    #         OrganizationService.create_membership_request(self.staff_user, AnonymousUser(), self.organization.id, membership_request)
    #     OrganizationService.create_membership_request(self.staff_user, self.staff_user, self.organization.id, membership_request)
    #     self.assertEqual(list(OrganizationService.get_membership_requests(self.organization_user, self.organization)), [membership_request])
    #     self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [self.organization])
    #
    #
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.accept_membership_request(AnonymousUser(), self.organization.id, membership_request)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.accept_membership_request(self.volunteer_user, self.organization.id, membership_request)
    #     OrganizationService.accept_membership_request(self.organization_user, self.organization.id, membership_request)
    #     self.assertEqual(OrganizationService.get_organization_membership_request(
    #         self.organization_user,
    #         self.organization.id,
    #         membership_request.id
    #     ).status, ReviewStatus.ACCEPTED)
    #     self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [])
    #     self.assertTrue(OrganizationService.user_is_organization_staff(self.staff_user, self.organization))
    #
    #     membership_request = OrganizationMembershipRequest()
    #     # We make sure the user is automatically replaced later with the right one
    #     membership_request.user = self.staff_user
    #     membership_request.role = OrgRole.STAFF
    #     OrganizationService.create_membership_request(self.organization_user, self.volunteer_user, self.organization.id, membership_request)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.reject_membership_request(AnonymousUser(), self.organization.id, membership_request)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.reject_membership_request(self.volunteer_user, self.organization.id, membership_request)
    #     with self.assertRaisesMessage(PermissionDenied, ''):
    #         OrganizationService.reject_membership_request(self.staff_user, self.organization.id, membership_request)
    #     OrganizationService.reject_membership_request(self.organization_user, self.organization.id, membership_request)
    #     self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [])
    #     self.assertFalse(OrganizationService.user_is_organization_member(self.volunteer_user, self.organization))
