from django.test import TestCase
from django.core.exceptions import PermissionDenied

from dssgmkt.models.user import User, UserType
from dssgmkt.models.org import Organization, OrganizationRole, Budget, YearsInOperation, SocialCause, GeographicalScope
from dssgmkt.domain.user import UserService
from dssgmkt.domain.org import OrganizationService

# Create your tests here.
class OrganizationTestCase(TestCase):
    organization_user = None
    volunteer_user = None
    organization = None

    def setUp(self):
        self.organization_user = User()
        self.organization_user.username = "OrgUser"
        self.organization_user.first_name = "Organization"
        self.organization_user.last_name = "User"
        UserService.create_user(None, self.organization_user, 'organization', None)

        self.volunteer_user = User()
        self.volunteer_user.username = "VolUser"
        self.volunteer_user.first_name = "Volunteer"
        self.volunteer_user.last_name = "User"
        UserService.create_user(None, self.volunteer_user, 'volunteer', None)

        self.organization = Organization()
        self.organization.name = "Organization A"
        self.organization.short_summary = "A short description of the org"
        self.organization.description = "A long form description of the organization"
        self.organization.website_url = "http://exampleorg.com"
        self.organization.phone_number = "(111)111-1111"
        self.organization.email_address = "email@org.org"
        self.organization.street_address = "1 One Street"
        self.organization.city = "OrgCity"
        self.organization.state = "OrgState"
        self.organization.zipcode = "11111"
        # self.organization.country = CountryField(verbose_name="Country")
        self.organization.budget = Budget.B100K
        self.organization.years_operation = YearsInOperation.Y0
        self.organization.main_cause = SocialCause.EDUCATION
        self.organization.organization_scope = GeographicalScope.LOCAL


    def test_false_assertion(self):
        if not self.organization_user:
            # This should never pass
            self.assertEqual(0, 1)

    def test_create_organization_by_volunteer_user(self):
        with self.assertRaisesMessage(PermissionDenied, ''):
            OrganizationService.create_organization(self.volunteer_user, self.organization)

    def test_create_organization_by_organization_user(self):
        all_organizations = OrganizationService.get_all_organizations(self.organization_user)
        self.assertFalse(all_organizations.exists())
        OrganizationService.create_organization(self.organization_user, self.organization)
        all_organizations = OrganizationService.get_all_organizations(self.organization_user)
        self.assertEquals(len(all_organizations), 1)
        self.assertEquals(all_organizations.first().name, self.organization.name)

    def test_create_duplicate_organization(self):
        with self.assertRaisesMessage(ValueError, 'An organization with this name already exists.'):
            OrganizationService.create_organization(self.organization_user, self.organization)
            OrganizationService.create_organization(self.organization_user, self.organization)

    def test_organization_roles(self):
        OrganizationService.create_organization(self.organization_user, self.organization)
        self.assertTrue(OrganizationService.user_is_organization_admin(self.organization_user, self.organization))
        self.assertTrue(OrganizationService.user_is_organization_member(self.organization_user, self.organization))
        self.assertFalse(OrganizationService.user_is_organization_admin(self.volunteer_user, self.organization))
        self.assertFalse(OrganizationService.user_is_organization_member(self.volunteer_user, self.organization))
