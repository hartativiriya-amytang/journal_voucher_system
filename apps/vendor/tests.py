from django.test import TestCase
from vendor.models import Vendor


class VendorTests(TestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(
            code='V001',
            name='Test Vendor',
            email='vendor@example.com',
            tax_id='1234567890',
        )

    def test_vendor_creation(self):
        self.assertEqual(str(self.vendor), '[V001] Test Vendor')
        self.assertEqual(self.vendor.is_active, 'ACTIVE')

    def test_default_credit_limit(self):
        self.assertEqual(self.vendor.credit_limit, 0)
