from django.test import TestCase
from master_data.models import Company, Branch, Currency


class CompanyTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            code='COMP001', name='Test Company', email='test@example.com'
        )

    def test_company_creation(self):
        self.assertEqual(str(self.company), '[COMP001] Test Company')
        self.assertEqual(self.company.is_active, 'ACTIVE')


class BranchTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(code='COMP001', name='Test Company')
        self.branch = Branch.objects.create(
            company=self.company, code='BR001', name='Test Branch'
        )

    def test_branch_creation(self):
        expected = f'[{self.company.code}-{self.branch.code}] {self.branch.name}'
        self.assertEqual(str(self.branch), expected)


class CurrencyTests(TestCase):
    def setUp(self):
        self.currency = Currency.objects.create(
            code='USD', name='US Dollar', symbol='$'
        )

    def test_currency_creation(self):
        self.assertEqual(str(self.currency), '[USD] US Dollar')
