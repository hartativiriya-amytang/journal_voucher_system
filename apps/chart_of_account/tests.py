from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from chart_of_account.models import ChartOfAccount
from common.constants import AccountType, NormalBalance, Status


class ChartOfAccountModelTests(TestCase):
    def setUp(self):
        self.parent = ChartOfAccount.objects.create(
            code='1', name='Assets', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT,
        )
        self.child = ChartOfAccount.objects.create(
            code='1.1', name='Cash', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT, parent=self.parent,
        )

    def test_str(self):
        self.assertEqual(str(self.parent), '[1] Assets')
        self.assertEqual(str(self.child), '[1.1] Cash')

    def test_parent_child_relationship(self):
        self.assertEqual(self.child.parent, self.parent)
        self.assertIn(self.child, self.parent.children.all())

    def test_default_is_active(self):
        self.assertEqual(self.parent.is_active, Status.ACTIVE)

    def test_unique_code(self):
        with self.assertRaises(IntegrityError):
            ChartOfAccount.objects.create(
                code='1', name='Duplicate', account_type=AccountType.ASSET,
                normal_balance=NormalBalance.DEBIT,
            )

    def test_description_default_blank(self):
        self.assertEqual(self.parent.description, '')

    def test_parent_nullable(self):
        account = ChartOfAccount.objects.create(
            code='2', name='Liabilities', account_type=AccountType.LIABILITY,
            normal_balance=NormalBalance.CREDIT,
        )
        self.assertIsNone(account.parent)

    def test_ordering_by_code(self):
        ChartOfAccount.objects.create(
            code='3', name='Revenue', account_type=AccountType.REVENUE,
            normal_balance=NormalBalance.CREDIT,
        )
        ChartOfAccount.objects.create(
            code='2', name='Expenses', account_type=AccountType.EXPENSE,
            normal_balance=NormalBalance.DEBIT,
        )
        accounts = list(ChartOfAccount.objects.filter(parent=None))
        self.assertEqual(accounts[0].code, '1')
        self.assertEqual(accounts[1].code, '2')
        self.assertEqual(accounts[2].code, '3')

    def test_all_account_types(self):
        for at, label in AccountType.choices:
            acc = ChartOfAccount.objects.create(
                code=f'T-{at}', name=f'Test {label}',
                account_type=at, normal_balance=NormalBalance.DEBIT,
            )
            self.assertEqual(acc.account_type, at)

    def test_all_normal_balances(self):
        for nb, label in NormalBalance.choices:
            acc = ChartOfAccount.objects.create(
                code=f'NB-{nb}', name=f'Test {label}',
                account_type=AccountType.ASSET, normal_balance=nb,
            )
            self.assertEqual(acc.normal_balance, nb)

    def test_delete_parent_cascades_to_children(self):
        child_pk = self.child.pk
        self.parent.delete()
        self.assertFalse(ChartOfAccount.objects.filter(pk=child_pk).exists())


class ChartOfAccountSerializerTests(TestCase):
    def setUp(self):
        self.parent = ChartOfAccount.objects.create(
            code='1', name='Assets', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT,
        )
        self.child = ChartOfAccount.objects.create(
            code='1.1', name='Cash', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT, parent=self.parent,
        )

    def test_serializer_includes_read_only_parent_fields(self):
        from chart_of_account.serializers import ChartOfAccountSerializer
        serializer = ChartOfAccountSerializer(self.child)
        self.assertEqual(serializer.data['parent_code'], '1')
        self.assertEqual(serializer.data['parent_name'], 'Assets')

    def test_serializer_includes_children_count(self):
        from chart_of_account.serializers import ChartOfAccountSerializer
        serializer = ChartOfAccountSerializer(self.parent)
        self.assertEqual(serializer.data['children_count'], 1)

    def test_serializer_parent_is_none_when_no_parent(self):
        from chart_of_account.serializers import ChartOfAccountSerializer
        serializer = ChartOfAccountSerializer(self.parent)
        self.assertIsNone(serializer.data['parent_code'])
        self.assertIsNone(serializer.data['parent_name'])

    def test_serializer_children_count_zero_when_no_children(self):
        from chart_of_account.serializers import ChartOfAccountSerializer
        serializer = ChartOfAccountSerializer(self.child)
        self.assertEqual(serializer.data['children_count'], 0)


class ChartOfAccountAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/chart-of-accounts/'

    def test_list_accounts(self):
        ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT,
        )
        ChartOfAccount.objects.create(
            code='2000', name='AP', account_type=AccountType.LIABILITY,
            normal_balance=NormalBalance.CREDIT,
        )
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 2)

    def test_create_account(self):
        resp = self.client.post(self.list_url, {
            'code': '3000', 'name': 'Equity',
            'account_type': 'EQUITY', 'normal_balance': 'CREDIT',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_create_account_with_parent(self):
        parent = ChartOfAccount.objects.create(
            code='4000', name='Revenue', account_type=AccountType.REVENUE,
            normal_balance=NormalBalance.CREDIT,
        )
        resp = self.client.post(self.list_url, {
            'code': '4100', 'name': 'Sales Revenue',
            'account_type': 'REVENUE', 'normal_balance': 'CREDIT',
            'parent': parent.id,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['parent_code'], '4000')

    def test_retrieve_includes_children_count(self):
        parent = ChartOfAccount.objects.create(
            code='5000', name='Expenses', account_type=AccountType.EXPENSE,
            normal_balance=NormalBalance.DEBIT,
        )
        ChartOfAccount.objects.create(
            code='5100', name='Rent', account_type=AccountType.EXPENSE,
            normal_balance=NormalBalance.DEBIT, parent=parent,
        )
        resp = self.client.get(f'{self.list_url}{parent.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['children_count'], 1)

    def test_update_account(self):
        acc = ChartOfAccount.objects.create(
            code='6000', name='Old', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT,
        )
        resp = self.client.patch(f'{self.list_url}{acc.id}/', {'name': 'New Name'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'New Name')

    def test_delete_account(self):
        acc = ChartOfAccount.objects.create(
            code='7000', name='Delete', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT,
        )
        resp = self.client.delete(f'{self.list_url}{acc.id}/')
        self.assertEqual(resp.status_code, 204)

    def test_search_accounts(self):
        ChartOfAccount.objects.create(
            code='8000', name='Inventory', account_type=AccountType.ASSET,
            normal_balance=NormalBalance.DEBIT,
        )
        resp = self.client.get(f'{self.list_url}?search=Inventory')
        self.assertEqual(len(resp.data['results']), 1)

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 403)
