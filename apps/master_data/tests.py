from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from master_data.models import Company, Branch, Currency


class CompanyModelTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            code='COMP001', name='Test Company', email='test@example.com'
        )

    def test_str(self):
        self.assertEqual(str(self.company), '[COMP001] Test Company')

    def test_default_is_active(self):
        self.assertEqual(self.company.is_active, 'ACTIVE')

    def test_unique_code(self):
        with self.assertRaises(IntegrityError):
            Company.objects.create(code='COMP001', name='Duplicate')

    def test_optional_fields_default_to_blank(self):
        c = Company.objects.create(code='MIN', name='Minimal')
        self.assertEqual(c.address, '')
        self.assertEqual(c.phone, '')
        self.assertEqual(c.email, '')

    def test_ordering(self):
        Company.objects.create(code='B', name='B')
        Company.objects.create(code='A', name='A')
        companies = list(Company.objects.all())
        self.assertEqual(companies[0].code, 'A')
        self.assertEqual(companies[1].code, 'B')


class BranchModelTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(code='COMP001', name='Test Company')
        self.branch = Branch.objects.create(
            company=self.company, code='BR001', name='Test Branch'
        )

    def test_str(self):
        expected = '[COMP001-BR001] Test Branch'
        self.assertEqual(str(self.branch), expected)

    def test_default_is_active(self):
        self.assertEqual(self.branch.is_active, 'ACTIVE')

    def test_unique_together_company_code(self):
        Branch.objects.create(company=self.company, code='BR002', name='Another')
        with self.assertRaises(IntegrityError):
            Branch.objects.create(company=self.company, code='BR001', name='Duplicate')

    def test_different_companies_can_have_same_code(self):
        other = Company.objects.create(code='COMP002', name='Other')
        branch = Branch.objects.create(company=other, code='BR001', name='Other Branch')
        self.assertEqual(branch.code, 'BR001')

    def test_cascade_delete(self):
        pk = self.company.pk
        self.company.delete()
        self.assertEqual(Branch.objects.filter(company_id=pk).count(), 0)


class CurrencyModelTests(TestCase):
    def setUp(self):
        self.currency = Currency.objects.create(
            code='USD', name='US Dollar', symbol='$'
        )

    def test_str(self):
        self.assertEqual(str(self.currency), '[USD] US Dollar')

    def test_default_is_active(self):
        self.assertEqual(self.currency.is_active, 'ACTIVE')

    def test_unique_code(self):
        with self.assertRaises(IntegrityError):
            Currency.objects.create(code='USD', name='Duplicate')

    def test_symbol_optional(self):
        c = Currency.objects.create(code='XYZ', name='Test Currency')
        self.assertEqual(c.symbol, '')


class CompanyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/master-data/companies/'

    def test_list_companies(self):
        Company.objects.create(code='C1', name='One')
        Company.objects.create(code='C2', name='Two')
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 2)

    def test_create_company(self):
        resp = self.client.post(self.list_url, {'code': 'NEW', 'name': 'New Co'}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['code'], 'NEW')

    def test_retrieve_company(self):
        c = Company.objects.create(code='RET', name='Retrieve Me')
        resp = self.client.get(f'{self.list_url}{c.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['code'], 'RET')

    def test_update_company(self):
        c = Company.objects.create(code='UPD', name='Old Name')
        resp = self.client.patch(f'{self.list_url}{c.id}/', {'name': 'New Name'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'New Name')

    def test_delete_company(self):
        c = Company.objects.create(code='DEL', name='Delete Me')
        resp = self.client.delete(f'{self.list_url}{c.id}/')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Company.objects.count(), 0)

    def test_search_companies(self):
        Company.objects.create(code='FIN', name='Finance Co')
        Company.objects.create(code='HR', name='HR Services')
        resp = self.client.get(f'{self.list_url}?search=Finance')
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['code'], 'FIN')

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 403)

    def test_serializer_includes_timestamps(self):
        c = Company.objects.create(code='TS', name='Timestamp')
        resp = self.client.get(f'{self.list_url}{c.id}/')
        self.assertIn('created_at', resp.data)
        self.assertIn('updated_at', resp.data)


class BranchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.company = Company.objects.create(code='C', name='Parent Co')
        self.list_url = '/api/master-data/branches/'

    def test_create_branch_with_read_only_fields(self):
        resp = self.client.post(self.list_url, {
            'company': self.company.id,
            'code': 'BR001',
            'name': 'Main Branch',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertIn('company_code', resp.data)
        self.assertIn('company_name', resp.data)
        self.assertEqual(resp.data['company_code'], 'C')
        self.assertEqual(resp.data['company_name'], 'Parent Co')

    def test_list_branches(self):
        Branch.objects.create(company=self.company, code='B1', name='Branch 1')
        Branch.objects.create(company=self.company, code='B2', name='Branch 2')
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 2)

    def test_delete_branch(self):
        b = Branch.objects.create(company=self.company, code='DEL', name='Delete')
        resp = self.client.delete(f'{self.list_url}{b.id}/')
        self.assertEqual(resp.status_code, 204)


class CurrencyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/master-data/currencies/'

    def test_create_currency(self):
        resp = self.client.post(self.list_url, {
            'code': 'EUR', 'name': 'Euro', 'symbol': '€',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_list_currencies(self):
        Currency.objects.create(code='USD', name='US Dollar')
        Currency.objects.create(code='EUR', name='Euro')
        resp = self.client.get(self.list_url)
        self.assertEqual(len(resp.data['results']), 2)

    def test_update_currency(self):
        c = Currency.objects.create(code='GBP', name='Pound')
        resp = self.client.patch(f'{self.list_url}{c.id}/', {'symbol': '£'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['symbol'], '£')
