from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from vendor.models import Vendor
from common.constants import Status


class VendorModelTests(TestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(
            code='V001', name='Test Vendor', email='vendor@example.com',
            tax_id='1234567890',
        )

    def test_str(self):
        self.assertEqual(str(self.vendor), '[V001] Test Vendor')

    def test_default_is_active(self):
        self.assertEqual(self.vendor.is_active, Status.ACTIVE)

    def test_default_credit_limit_zero(self):
        self.assertEqual(self.vendor.credit_limit, 0)

    def test_unique_code(self):
        with self.assertRaises(IntegrityError):
            Vendor.objects.create(code='V001', name='Duplicate')

    def test_optional_fields_default_to_blank(self):
        v = Vendor.objects.create(code='V-MIN', name='Minimal')
        self.assertEqual(v.address, '')
        self.assertEqual(v.phone, '')
        self.assertEqual(v.email, '')
        self.assertEqual(v.tax_id, '')
        self.assertEqual(v.bank_account, '')
        self.assertEqual(v.payment_terms, '')

    def test_ordering_by_code(self):
        Vendor.objects.create(code='B', name='Vendor B')
        Vendor.objects.create(code='A', name='Vendor A')
        vendors = list(Vendor.objects.all())
        self.assertEqual(vendors[0].code, 'A')
        self.assertEqual(vendors[1].code, 'B')

    def test_credit_limit_decimal(self):
        from decimal import Decimal
        v = Vendor.objects.create(code='V-CR', name='Credit Test', credit_limit=Decimal('50000.00'))
        self.assertEqual(v.credit_limit, Decimal('50000.00'))


class VendorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/vendors/'

    def test_list_vendors(self):
        Vendor.objects.create(code='V1', name='Vendor 1')
        Vendor.objects.create(code='V2', name='Vendor 2')
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 2)

    def test_create_vendor(self):
        resp = self.client.post(self.list_url, {
            'code': 'V-NEW', 'name': 'New Vendor', 'email': 'new@vendor.com',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['code'], 'V-NEW')

    def test_create_vendor_with_all_fields(self):
        resp = self.client.post(self.list_url, {
            'code': 'V-FULL', 'name': 'Full Vendor',
            'address': '123 Main St', 'phone': '555-0100',
            'email': 'full@vendor.com', 'tax_id': 'TAX-123',
            'bank_account': 'BNK-456', 'credit_limit': '25000.00',
            'payment_terms': 'Net 30',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['credit_limit'], '25000.00')

    def test_retrieve_vendor(self):
        v = Vendor.objects.create(code='V-RET', name='Retrieve Me')
        resp = self.client.get(f'{self.list_url}{v.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['code'], 'V-RET')

    def test_update_vendor(self):
        v = Vendor.objects.create(code='V-UPD', name='Old Name')
        resp = self.client.patch(f'{self.list_url}{v.id}/', {'name': 'Updated'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'Updated')

    def test_delete_vendor(self):
        v = Vendor.objects.create(code='V-DEL', name='Delete Me')
        resp = self.client.delete(f'{self.list_url}{v.id}/')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_search_vendors(self):
        Vendor.objects.create(code='V-TAX', name='Tax Services', email='tax@svc.com')
        resp = self.client.get(f'{self.list_url}?search=Tax')
        self.assertEqual(len(resp.data['results']), 1)

    def test_search_by_email(self):
        Vendor.objects.create(code='V-EM', name='Email Test', email='findme@test.com')
        resp = self.client.get(f'{self.list_url}?search=findme')
        self.assertEqual(len(resp.data['results']), 1)

    def test_search_by_tax_id(self):
        Vendor.objects.create(code='V-TID', name='Tax ID Test', tax_id='TAX999')
        resp = self.client.get(f'{self.list_url}?search=TAX999')
        self.assertEqual(len(resp.data['results']), 1)

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 403)

    def test_timestamps_in_response(self):
        v = Vendor.objects.create(code='V-TS', name='Timestamps')
        resp = self.client.get(f'{self.list_url}{v.id}/')
        self.assertIn('created_at', resp.data)
        self.assertIn('updated_at', resp.data)
