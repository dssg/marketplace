from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from dssgmkt.models.common import ReviewStatus
from dssgmkt.models.user import User, UserType
from dssgmkt.models.org import Organization, OrganizationRole, OrganizationSocialCause, Budget, YearsInOperation, SocialCause, GeographicalScope, OrganizationMembershipRequest, OrgRole
from dssgmkt.domain.user import UserService
from dssgmkt.domain.org import OrganizationService

from dssgmkt.tests.domain.common import (
    example_organization_user, example_staff_user, example_volunteer_user,
    example_organization,
    test_users_group_inclusion, test_permission_denied_operation,
)

class OrganizationTestCase(TestCase):
    organization_user = None
    staff_user = None
    volunteer_user = None
    organization = None

    def setUp(self):
        self.organization_user = example_organization_user()
        UserService.create_user(None, self.organization_user, 'organization', None)
        self.staff_user = example_staff_user()
        UserService.create_user(None, self.staff_user, 'organization', None)
        self.volunteer_user = example_volunteer_user()
        UserService.create_user(None, self.volunteer_user, 'volunteer', None)

        self.organization = example_organization()

    def test_create_organization(self):
        all_organizations = OrganizationService.get_all_organizations(self.organization_user)
        with self.subTest(stage='No starting organizations'):
            self.assertFalse(all_organizations.exists())


        with self.subTest(stage='Create organization'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: OrganizationService.create_organization(x, self.organization))
            OrganizationService.create_organization(self.organization_user, self.organization)

        all_organizations = OrganizationService.get_all_organizations(self.organization_user)
        saved_organization = OrganizationService.get_organization(self.organization_user, self.organization.id)

        with self.subTest(stage='Test created organization'):
            self.assertEqual(len(all_organizations), 1)
            self.assertEqual(all_organizations.first().name, self.organization.name)
            self.assertEqual(all_organizations.first(), saved_organization)
            self.assertEqual(
                list(OrganizationService.get_all_organizations(AnonymousUser())),
                list(OrganizationService.get_all_organizations(self.organization_user)),
            )
            self.assertEqual(
                saved_organization,
                OrganizationService.get_organization(AnonymousUser(), self.organization.id),
            )
            self.assertEqual(OrganizationService.get_featured_organization(), self.organization)

    def test_edit_organization(self):
        OrganizationService.create_organization(self.organization_user, self.organization)
        self.organization.name = "EDITED Organization A"
        self.organization.short_summary = "EDITED A short description of the org"
        self.organization.description = "EDITED A long form description of the organization"
        self.organization.website_url = "http://exampleorg.com/EDITED"
        self.organization.phone_number = "(111)111-EDITED"
        self.organization.email_address = "EDITEDemail@org.org"
        self.organization.street_address = "EDITED 1 One Street"
        self.organization.city = "EDITED OrgCity"
        self.organization.state = "EDITED OrgState"
        self.organization.zipcode = "EDITED11111"
        self.organization.budget = Budget.B50MP
        self.organization.years_operation = YearsInOperation.Y25
        self.organization.organization_scope = GeographicalScope.COUNTRY

        with self.subTest(stage='Add staff member'):
            OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)

        with self.subTest(stage='Edit organization'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
                lambda x: OrganizationService.save_organization_info(x, self.organization.id, self.organization))
            OrganizationService.save_organization_info(self.organization_user, self.organization.id, self.organization)
            self.assertEqual(self.organization, OrganizationService.get_organization(self.organization_user, self.organization.id))


    def test_filter_organization(self):
        OrganizationService.create_organization(self.organization_user, self.organization)
        sc = OrganizationSocialCause()
        sc.social_cause = SocialCause.EDUCATION
        sc.organization = self.organization
        sc.save()
        org_result_list = [self.organization]
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'name': 'ORGAN'})), org_result_list)
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'name': 'no match'})), [])
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'name': ' A'})), org_result_list)
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'social_cause': 'education'})), org_result_list)
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'social_cause': ['education', 'health']})), org_result_list)
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'social_cause': ['health']})), [])
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'project_status': 'new'})), [])
        self.assertEqual(list(OrganizationService.get_all_organizations(self.organization_user, {'project_status': ['new', 'completed']})), [])

    def test_create_duplicate_organization(self):
        with self.assertRaisesMessage(ValueError, 'An organization with this name already exists.'):
            OrganizationService.create_organization(self.organization_user, self.organization)
            OrganizationService.create_organization(self.organization_user, self.organization)

    def test_organization_roles(self):
        OrganizationService.create_organization(self.organization_user, self.organization)
        with self.subTest(stage='Check initial organization user\'s roles'):
            self.assertTrue(OrganizationService.user_is_organization_admin(self.organization_user, self.organization))
            self.assertTrue(OrganizationService.user_is_organization_member(self.organization_user, self.organization))
            self.assertFalse(OrganizationService.user_is_organization_staff(self.organization_user, self.organization))
            self.assertTrue(OrganizationService.user_is_any_organization_member(self.organization_user))

        with self.subTest(stage='Check initial volunteer user\'s roles'):
            self.assertFalse(OrganizationService.user_is_organization_admin(self.volunteer_user, self.organization))
            self.assertFalse(OrganizationService.user_is_organization_member(self.volunteer_user, self.organization))
            self.assertFalse(OrganizationService.user_is_organization_staff(self.volunteer_user, self.organization))
            self.assertFalse(OrganizationService.user_is_any_organization_member(self.volunteer_user))

        with self.subTest(stage='Add staff member'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
                lambda x: OrganizationService.add_staff_member_by_id(x, self.organization.id, self.staff_user.id, None))
            OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)

        with self.subTest(stage='Check staff user\'s roles'):
            self.assertFalse(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
            self.assertTrue(OrganizationService.user_is_organization_member(self.staff_user, self.organization))
            self.assertTrue(OrganizationService.user_is_organization_staff(self.staff_user, self.organization))
            self.assertTrue(OrganizationService.user_is_any_organization_member(self.staff_user))


        with self.subTest(stage='Check organization group roles'):
            organization_staff_roles = OrganizationService.get_organization_staff(self.organization_user, self.organization)
            org_admin_user_role = OrganizationService.get_organization_role(self.organization_user, self.organization.id, self.organization_user.id)
            org_staff_user_role = OrganizationService.get_organization_role(self.organization_user, self.organization.id, self.staff_user.id)
            self.assertEqual(list(organization_staff_roles), [
                org_admin_user_role,
                org_staff_user_role,
            ])
            self.assertEqual(org_admin_user_role, OrganizationService.get_organization_role_by_pk(self.organization_user, self.organization.id, org_admin_user_role.id))
            self.assertEqual(org_staff_user_role, OrganizationService.get_organization_role_by_pk(self.organization_user, self.organization.id, org_staff_user_role.id))

        with self.subTest(stage='Check organization members'):
            organization_members = OrganizationService.get_organization_members(self.organization_user, self.organization)
            self.assertEqual(set(organization_members), set([self.organization_user, self.staff_user]))

        with self.subTest(stage='Check organization admins'):
            organization_admins = OrganizationService.get_organization_admins(self.organization_user, self.organization)
            self.assertEqual(set(organization_admins), set([self.organization_user]))

        with self.subTest(stage='Check non members'):
            volunteer_user_match = {
                'id': self.volunteer_user.id,
                'first_name': self.volunteer_user.first_name,
                'last_name': self.volunteer_user.last_name,
                'username': self.volunteer_user.username,
            }
            self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id)), [volunteer_user_match])
            self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "olu")), [volunteer_user_match])
            self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "volunteer")), [volunteer_user_match])
            self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "use")), [volunteer_user_match])
            self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "eer@ema")), [volunteer_user_match])
            self.assertEqual(list(OrganizationService.get_all_users_not_organization_members(self.organization.id, "bad_match")), [])

        with self.subTest(stage='Leave organization'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.organization_user],
                lambda x: OrganizationService.leave_organization(x, self.organization.id, org_staff_user_role))
            OrganizationService.leave_organization(self.staff_user, self.organization.id, org_staff_user_role)
            self.assertFalse(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
            self.assertFalse(OrganizationService.user_is_organization_member(self.staff_user, self.organization))
            self.assertFalse(OrganizationService.user_is_organization_staff(self.staff_user, self.organization))
            self.assertFalse(OrganizationService.user_is_any_organization_member(self.staff_user))
            with self.assertRaisesMessage(OrganizationRole.DoesNotExist, 'OrganizationRole matching query does not exist.'):
                OrganizationService.get_organization_role(self.organization_user, self.organization.id, self.staff_user.id)

        with self.subTest(stage='Add staff member'):
            test_permission_denied_operation(self, [AnonymousUser(), self.staff_user],
                lambda x: OrganizationService.add_staff_member(x, self.organization.id, org_staff_user_role))
            OrganizationService.add_staff_member(self.organization_user, self.organization.id, org_staff_user_role)

        with self.subTest(stage='Edit organization role'):
            org_staff_user_role.role = OrgRole.ADMINISTRATOR
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
                lambda x: OrganizationService.save_organization_role(x, self.organization.id, org_staff_user_role))
            OrganizationService.save_organization_role(self.organization_user, self.organization.id, org_staff_user_role)
            self.assertTrue(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))

        with self.subTest(stage='Delete organization role'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: OrganizationService.delete_organization_role(x, self.organization.id, org_staff_user_role))
            OrganizationService.delete_organization_role(self.organization_user, self.organization.id, org_staff_user_role)
            self.assertFalse(OrganizationService.user_is_organization_admin(self.staff_user, self.organization))
            self.assertFalse(OrganizationService.user_is_organization_member(self.staff_user, self.organization))

    def test_create_duplicate_role(self):
        OrganizationService.create_organization(self.organization_user, self.organization)
        OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)
        with self.assertRaisesMessage(ValueError, ''):
            OrganizationService.add_staff_member_by_id(self.organization_user, self.organization.id, self.staff_user.id, None)

    def test_organization_membership_requests(self):
        OrganizationService.create_organization(self.organization_user, self.organization)
        with self.subTest(stage='Initial membership requests'):
            self.assertEqual(list(OrganizationService.get_membership_requests(self.organization_user, self.organization)), [])
            self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [])

        membership_request = OrganizationMembershipRequest()
        membership_request.user = self.staff_user
        membership_request.role = OrgRole.STAFF

        with self.subTest(stage='Create membership request'):
            with self.assertRaisesMessage(ValueError, ''):
                OrganizationService.create_membership_request(self.staff_user, AnonymousUser(), self.organization.id, membership_request)
            OrganizationService.create_membership_request(self.staff_user, self.staff_user, self.organization.id, membership_request)
            self.assertEqual(list(OrganizationService.get_membership_requests(self.organization_user, self.organization)), [membership_request])
            self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [self.organization])


        with self.subTest(stage='Accept membership request'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: OrganizationService.accept_membership_request(x, self.organization.id, membership_request))
            OrganizationService.accept_membership_request(self.organization_user, self.organization.id, membership_request)
            self.assertEqual(OrganizationService.get_organization_membership_request(
                self.organization_user,
                self.organization.id,
                membership_request.id
            ).status, ReviewStatus.ACCEPTED)
            self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [])
            self.assertTrue(OrganizationService.user_is_organization_staff(self.staff_user, self.organization))

        membership_request = OrganizationMembershipRequest()
        membership_request.user = self.staff_user # We make sure the user is automatically replaced later with the right one
        membership_request.role = OrgRole.STAFF

        with self.subTest(stage='Reject membership request'):
            OrganizationService.create_membership_request(self.organization_user, self.volunteer_user, self.organization.id, membership_request)
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
                lambda x: OrganizationService.reject_membership_request(x, self.organization.id, membership_request))
            OrganizationService.reject_membership_request(self.organization_user, self.organization.id, membership_request)
            self.assertEqual(list(OrganizationService.get_user_organizations_with_pending_requests(self.organization_user)), [])
            self.assertFalse(OrganizationService.user_is_organization_member(self.volunteer_user, self.organization))
