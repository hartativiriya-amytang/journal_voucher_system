from django.test import TestCase
from chart_of_account.models import ChartOfAccount


class ChartOfAccountTests(TestCase):
    def setUp(self):
        self.parent = ChartOfAccount.objects.create(
            code='1', name='Assets', account_type='ASSET', normal_balance='DEBIT'
        )
        self.child = ChartOfAccount.objects.create(
            code='1.1', name='Cash', account_type='ASSET',
            normal_balance='DEBIT', parent=self.parent
        )

    def test_account_creation(self):
        self.assertEqual(str(self.parent), '[1] Assets')

    def test_hierarchy(self):
        self.assertEqual(self.child.parent, self.parent)
        self.assertIn(self.child, self.parent.children.all())
