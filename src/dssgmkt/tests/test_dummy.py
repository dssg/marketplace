from django.test import TestCase


# Create your tests here.
class DummyTestCase(TestCase):
    def setUp(self):
        super.setUp()

    def test_false_assertion(self):
        # This should never pass
        self.assertEqual(0, 1)
