from django.test import TestCase


# Create your tests here.
class OrganizationTestCase(TestCase):
    def setUp(self):
        organization_user = User()
        organization_user.initial_type = UserType.
        pass

    def test_false_assertion(self):
        # This should never pass
        self.assertEqual(0, 1)
