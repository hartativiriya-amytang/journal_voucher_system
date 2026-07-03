from decimal import Decimal
from datetime import date, datetime
from io import BytesIO
from openpyxl import Workbook
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from common.constants import PeriodStatus, Status, VoucherStatus
from accounting_period.models import AccountingPeriod
from chart_of_account.models import ChartOfAccount
from vendor.models import Vendor
from journal_voucher.models import JournalVoucher, JournalEntry
from journal_voucher.validators import (
    validate_debit_credit_balance,
    validate_period_open,
    validate_account_active,
)


class JournalVoucherModelTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET', normal_balance='DEBIT',
        )
        self.account2 = ChartOfAccount.objects.create(
            code='4000', name='Revenue', account_type='REVENUE', normal_balance='CREDIT',
        )
        self.vendor = Vendor.objects.create(code='V001', name='Test Vendor')
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')

    def test_create_voucher_generates_number(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='Test voucher',
        )
        self.assertTrue(voucher.voucher_number.startswith('JV-'))
        self.assertEqual(voucher.status, VoucherStatus.DRAFT)
        self.assertEqual(voucher.total_debit, 0)
        self.assertEqual(voucher.total_credit, 0)

    def test_transaction_date_within_period(self):
        with self.assertRaises(ValidationError):
            JournalVoucher.objects.create(
                accounting_period=self.period, transaction_date=date(2026, 2, 1),
                description='Out of period',
            )

    def test_transaction_date_on_boundaries(self):
        voucher_start = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 1),
            description='Start boundary',
        )
        self.assertEqual(voucher_start.transaction_date, date(2026, 1, 1))
        voucher_end = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 31),
            description='End boundary',
        )
        self.assertEqual(voucher_end.transaction_date, date(2026, 1, 31))

    def test_voucher_str(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='Test voucher',
        )
        self.assertIn(voucher.voucher_number, str(voucher))
        self.assertIn('Test voucher', str(voucher))

    def test_voucher_number_increment(self):
        v1 = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='First',
        )
        v2 = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='Second',
        )
        num1 = int(v1.voucher_number.split('-')[-1])
        num2 = int(v2.voucher_number.split('-')[-1])
        self.assertEqual(num2, num1 + 1)

    def test_optional_vendor_bl_invoice(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='Minimal',
        )
        self.assertIsNone(voucher.vendor)
        self.assertEqual(voucher.bl_number, '')
        self.assertEqual(voucher.invoice_number, '')

    def test_created_by_nullable(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='No creator',
        )
        self.assertIsNone(voucher.created_by)


class JournalEntryModelTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET', normal_balance='DEBIT',
        )
        self.voucher = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='Test voucher',
        )

    def test_entry_requires_debit_or_credit(self):
        with self.assertRaises(ValidationError):
            JournalEntry.objects.create(
                voucher=self.voucher, account=self.account, debit=0, credit=0,
            )

    def test_entry_cannot_have_both_debit_and_credit(self):
        with self.assertRaises(ValidationError):
            JournalEntry.objects.create(
                voucher=self.voucher, account=self.account, debit=100, credit=100,
            )

    def test_valid_entry_debit(self):
        entry = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=Decimal('100.00'), credit=0,
        )
        self.assertEqual(entry.debit, Decimal('100.00'))
        self.assertEqual(entry.credit, 0)
        self.assertEqual(entry.line_order, 0)

    def test_valid_entry_credit(self):
        entry = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=0, credit=Decimal('100.00'),
        )
        self.assertEqual(entry.debit, 0)
        self.assertEqual(entry.credit, Decimal('100.00'))

    def test_entry_str(self):
        entry = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=Decimal('100.00'), credit=0,
        )
        expected = f'{self.voucher.voucher_number} - {self.account.code}: 100.00/0'
        self.assertEqual(str(entry), expected)

    def test_entry_default_line_order(self):
        e1 = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account, debit=100, credit=0,
        )
        e2 = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account, debit=0, credit=100,
        )
        self.assertEqual(e1.line_order, 0)
        self.assertEqual(e2.line_order, 0)

    def test_entries_ordered_by_line_order(self):
        JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=100, credit=0, line_order=2,
        )
        JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=0, credit=100, line_order=1,
        )
        entries = list(self.voucher.entries.all())
        self.assertEqual(entries[0].line_order, 1)
        self.assertEqual(entries[1].line_order, 2)

    def test_voucher_cascade_deletes_entries(self):
        JournalEntry.objects.create(
            voucher=self.voucher, account=self.account, debit=100, credit=0,
        )
        JournalEntry.objects.create(
            voucher=self.voucher, account=self.account, debit=0, credit=100,
        )
        pk = self.voucher.pk
        self.voucher.delete()
        self.assertEqual(JournalEntry.objects.filter(voucher_id=pk).count(), 0)

    def test_description_optional(self):
        entry = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account, debit=100, credit=0,
        )
        self.assertEqual(entry.description, '')


class ValidatorTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.active_account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET',
            normal_balance='DEBIT', is_active=Status.ACTIVE,
        )
        self.inactive_account = ChartOfAccount.objects.create(
            code='2000', name='Old Account', account_type='LIABILITY',
            normal_balance='CREDIT', is_active=Status.INACTIVE,
        )

    def test_validate_debit_credit_balance_equal(self):
        entries = [
            type('Entry', (), {'debit': Decimal('100'), 'credit': Decimal('0')})(),
            type('Entry', (), {'debit': Decimal('0'), 'credit': Decimal('100')})(),
        ]
        total_d, total_c = validate_debit_credit_balance(entries)
        self.assertEqual(total_d, Decimal('100'))
        self.assertEqual(total_c, Decimal('100'))

    def test_validate_debit_credit_balance_unequal(self):
        entries = [
            type('Entry', (), {'debit': Decimal('100'), 'credit': Decimal('0')})(),
            type('Entry', (), {'debit': Decimal('0'), 'credit': Decimal('50')})(),
        ]
        with self.assertRaises(ValidationError):
            validate_debit_credit_balance(entries)

    def test_validate_debit_credit_with_dicts(self):
        entries = [
            {'debit': Decimal('200'), 'credit': Decimal('0')},
            {'debit': Decimal('0'), 'credit': Decimal('200')},
        ]
        total_d, total_c = validate_debit_credit_balance(entries)
        self.assertEqual(total_d, Decimal('200'))
        self.assertEqual(total_c, Decimal('200'))

    def test_validate_handles_none_values(self):
        entries = [
            {'debit': None, 'credit': Decimal('100')},
            {'debit': Decimal('100'), 'credit': None},
        ]
        total_d, total_c = validate_debit_credit_balance(entries)
        self.assertEqual(total_d, Decimal('100'))
        self.assertEqual(total_c, Decimal('100'))

    def test_validate_period_open(self):
        validate_period_open(self.period)

    def test_validate_period_closed(self):
        self.period.status = PeriodStatus.CLOSED
        with self.assertRaises(ValidationError):
            validate_period_open(self.period)

    def test_validate_account_active(self):
        validate_account_active(self.active_account)

    def test_validate_account_inactive(self):
        with self.assertRaises(ValidationError):
            validate_account_active(self.inactive_account)


class JournalVoucherSerializerTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET', normal_balance='DEBIT',
        )
        self.user = User.objects.create_user('seruser', 'ser@test.com', 'pass')

    def test_serializer_validates_empty_entries(self):
        from journal_voucher.serializers import JournalVoucherSerializer
        serializer = JournalVoucherSerializer(data={
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Test',
            'entries': [],
        }, context={'request': type('Req', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn('entries', serializer.errors)

    def test_serializer_validates_entry_with_both_debit_credit(self):
        from journal_voucher.serializers import JournalVoucherSerializer
        serializer = JournalVoucherSerializer(data={
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Test',
            'entries': [{'account': self.account.id, 'debit': 100, 'credit': 100}],
        }, context={'request': type('Req', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())

    def test_serializer_validates_entry_with_no_amount(self):
        from journal_voucher.serializers import JournalVoucherSerializer
        serializer = JournalVoucherSerializer(data={
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Test',
            'entries': [{'account': self.account.id, 'debit': 0, 'credit': 0}],
        }, context={'request': type('Req', (), {'user': self.user})()})
        self.assertFalse(serializer.is_valid())

    def test_serializer_valid_data_passes(self):
        from journal_voucher.serializers import JournalVoucherSerializer
        serializer = JournalVoucherSerializer(data={
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Test',
            'entries': [
                {'account': self.account.id, 'debit': '100.00', 'credit': '0'},
                {'account': self.account.id, 'debit': '0', 'credit': '100.00'},
            ],
        }, context={'request': type('Req', (), {'user': self.user})()})
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)


class JournalVoucherAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET', normal_balance='DEBIT',
        )
        self.account2 = ChartOfAccount.objects.create(
            code='4000', name='Revenue', account_type='REVENUE', normal_balance='CREDIT',
        )
        self.list_url = '/api/journal-vouchers/'

    def _valid_payload(self):
        return {
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Test voucher',
            'entries': [
                {'account': self.account.id, 'debit': '100.00', 'credit': '0'},
                {'account': self.account2.id, 'debit': '0', 'credit': '100.00'},
            ],
        }

    def test_create_voucher(self):
        resp = self.client.post(self.list_url, self._valid_payload(), format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data['voucher_number'].startswith('JV-'))
        self.assertEqual(resp.data['total_debit'], '100.00')
        self.assertEqual(resp.data['total_credit'], '100.00')
        self.assertEqual(len(resp.data['entries']), 2)

    def test_create_voucher_sets_created_by(self):
        resp = self.client.post(self.list_url, self._valid_payload(), format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['created_by_username'], 'apiuser')

    def test_list_vouchers(self):
        self.client.post(self.list_url, self._valid_payload(), format='json')
        self.client.post(self.list_url, self._valid_payload(), format='json')
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 2)

    def test_list_uses_list_serializer(self):
        self.client.post(self.list_url, self._valid_payload(), format='json')
        resp = self.client.get(self.list_url)
        self.assertIn('accounting_period_name', resp.data['results'][0])
        self.assertNotIn('entries', resp.data['results'][0])

    def test_retrieve_voucher(self):
        create_resp = self.client.post(self.list_url, self._valid_payload(), format='json')
        pk = create_resp.data['id']
        resp = self.client.get(f'{self.list_url}{pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('entries', resp.data)

    def test_update_voucher_replaces_entries(self):
        create_resp = self.client.post(self.list_url, self._valid_payload(), format='json')
        pk = create_resp.data['id']
        resp = self.client.put(f'{self.list_url}{pk}/', {
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-20',
            'description': 'Updated',
            'entries': [
                {'account': self.account.id, 'debit': '200.00', 'credit': '0'},
                {'account': self.account2.id, 'debit': '0', 'credit': '200.00'},
            ],
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['total_debit'], '200.00')
        self.assertEqual(resp.data['description'], 'Updated')

    def test_partial_update_voucher(self):
        create_resp = self.client.post(self.list_url, self._valid_payload(), format='json')
        pk = create_resp.data['id']
        resp = self.client.patch(f'{self.list_url}{pk}/', {'description': 'Partially Updated'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['description'], 'Partially Updated')

    def test_delete_voucher(self):
        create_resp = self.client.post(self.list_url, self._valid_payload(), format='json')
        pk = create_resp.data['id']
        resp = self.client.delete(f'{self.list_url}{pk}/')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(JournalVoucher.objects.count(), 0)

    def test_search_vouchers(self):
        self.client.post(self.list_url, self._valid_payload(), format='json')
        resp = self.client.get(f'{self.list_url}?search=Test voucher')
        self.assertEqual(len(resp.data['results']), 1)

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 403)


class JournalVoucherValidateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET', normal_balance='DEBIT',
        )
        self.account2 = ChartOfAccount.objects.create(
            code='4000', name='Revenue', account_type='REVENUE', normal_balance='CREDIT',
        )
        self.list_url = '/api/journal-vouchers/'

    def _create_draft_voucher(self):
        resp = self.client.post(self.list_url, {
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Test',
            'entries': [
                {'account': self.account.id, 'debit': '100.00', 'credit': '0'},
                {'account': self.account2.id, 'debit': '0', 'credit': '100.00'},
            ],
        }, format='json')
        return resp.data['id']

    def test_validate_draft_voucher_succeeds(self):
        pk = self._create_draft_voucher()
        resp = self.client.post(f'{self.list_url}{pk}/validate/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], VoucherStatus.VALIDATED)

    def test_validate_already_validated_fails(self):
        pk = self._create_draft_voucher()
        self.client.post(f'{self.list_url}{pk}/validate/')
        resp = self.client.post(f'{self.list_url}{pk}/validate/')
        self.assertEqual(resp.status_code, 400)

    def test_validate_voided_voucher_fails(self):
        pk = self._create_draft_voucher()
        self.client.post(f'{self.list_url}{pk}/void/')
        resp = self.client.post(f'{self.list_url}{pk}/validate/')
        self.assertEqual(resp.status_code, 400)

    def test_validate_voucher_without_entries_fails(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period, transaction_date=date(2026, 1, 15),
            description='Empty voucher',
        )
        resp = self.client.post(f'{self.list_url}{voucher.id}/validate/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no entries', resp.data['error'].lower())

    def test_validate_voucher_with_imbalanced_entries_fails(self):
        resp = self.client.post(self.list_url, {
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Imbalanced',
            'entries': [
                {'account': self.account.id, 'debit': '200.00', 'credit': '0'},
                {'account': self.account2.id, 'debit': '0', 'credit': '100.00'},
            ],
        }, format='json')
        pk = resp.data['id']
        resp = self.client.post(f'{self.list_url}{pk}/validate/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('errors', resp.data)

    def test_validate_voucher_with_inactive_account_fails(self):
        inactive = ChartOfAccount.objects.create(
            code='9999', name='Old', account_type='ASSET',
            normal_balance='DEBIT', is_active=Status.INACTIVE,
        )
        resp = self.client.post(self.list_url, {
            'accounting_period': self.period.id,
            'transaction_date': '2026-01-15',
            'description': 'Inactive',
            'entries': [
                {'account': inactive.id, 'debit': '100.00', 'credit': '0'},
                {'account': self.account2.id, 'debit': '0', 'credit': '100.00'},
            ],
        }, format='json')
        pk = resp.data['id']
        resp = self.client.post(f'{self.list_url}{pk}/validate/')
        self.assertEqual(resp.status_code, 400)

    def test_validate_voucher_with_closed_period_fails(self):
        closed_period = AccountingPeriod.objects.create(
            code='202501', name='Jan 2025',
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
            status=PeriodStatus.CLOSED,
        )
        resp = self.client.post(self.list_url, {
            'accounting_period': closed_period.id,
            'transaction_date': '2025-01-15',
            'description': 'Closed',
            'entries': [
                {'account': self.account.id, 'debit': '100.00', 'credit': '0'},
                {'account': self.account2.id, 'debit': '0', 'credit': '100.00'},
            ],
        }, format='json')
        pk = resp.data['id']
        resp = self.client.post(f'{self.list_url}{pk}/validate/')
        self.assertEqual(resp.status_code, 400)

    def test_void_draft_voucher_succeeds(self):
        pk = self._create_draft_voucher()
        resp = self.client.post(f'{self.list_url}{pk}/void/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], VoucherStatus.VOID)

    def test_void_already_voided_fails(self):
        pk = self._create_draft_voucher()
        self.client.post(f'{self.list_url}{pk}/void/')
        resp = self.client.post(f'{self.list_url}{pk}/void/')
        self.assertEqual(resp.status_code, 400)

    def test_void_validated_voucher_succeeds(self):
        pk = self._create_draft_voucher()
        self.client.post(f'{self.list_url}{pk}/validate/')
        resp = self.client.post(f'{self.list_url}{pk}/void/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], VoucherStatus.VOID)


class ExcelUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET', normal_balance='DEBIT',
        )
        self.account2 = ChartOfAccount.objects.create(
            code='4000', name='Revenue', account_type='REVENUE', normal_balance='CREDIT',
        )
        self.url = '/api/journal-vouchers/upload_excel/'

    def _make_excel(self, rows):
        wb = Workbook()
        ws = wb.active
        ws.append(['Voucher Description', 'Account Code', 'Debit', 'Credit',
                    'Line Description', 'Transaction Date', 'Accounting Period Code'])
        for row in rows:
            ws.append(row)
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        return bio

    def test_upload_creates_vouchers(self):
        excel = self._make_excel([
            ['Test Voucher', '1000', '500.00', '', 'Cash', '2026-01-15', '202601'],
            ['Test Voucher', '4000', '', '500.00', 'Revenue', '2026-01-15', '202601'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['created'], 1)
        self.assertEqual(len(resp.data['errors']), 0)

    def test_upload_creates_multiple_vouchers(self):
        excel = self._make_excel([
            ['Voucher 1', '1000', '100.00', '', '', '2026-01-15', '202601'],
            ['Voucher 1', '4000', '', '100.00', '', '2026-01-15', '202601'],
            ['Voucher 2', '1000', '200.00', '', '', '2026-01-16', '202601'],
            ['Voucher 2', '4000', '', '200.00', '', '2026-01-16', '202601'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['created'], 2)

    def test_upload_imbalanced_entries_reports_error(self):
        excel = self._make_excel([
            ['Bad Voucher', '1000', '100.00', '', '', '2026-01-15', '202601'],
            ['Bad Voucher', '4000', '', '50.00', '', '2026-01-15', '202601'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.data['created'], 0)
        self.assertEqual(len(resp.data['errors']), 1)

    def test_upload_nonexistent_account_reports_error(self):
        excel = self._make_excel([
            ['Bad Acct', '9999', '100.00', '', '', '2026-01-15', '202601'],
            ['Bad Acct', '4000', '', '100.00', '', '2026-01-15', '202601'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.data['created'], 0)
        self.assertEqual(len(resp.data['errors']), 1)

    def test_upload_nonexistent_period_reports_error(self):
        excel = self._make_excel([
            ['Bad Period', '1000', '100.00', '', '', '2026-01-15', 'NONEXISTENT'],
            ['Bad Period', '4000', '', '100.00', '', '2026-01-15', 'NONEXISTENT'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.data['created'], 0)
        self.assertEqual(len(resp.data['errors']), 1)

    def test_upload_empty_file_returns_error(self):
        excel = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.append(['Header'])
        wb.save(excel)
        excel.seek(0)
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.status_code, 400)

    def test_upload_no_file_returns_error(self):
        resp = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(resp.status_code, 400)

    def test_upload_skips_empty_description_rows(self):
        excel = self._make_excel([
            ['', '1000', '100.00', '', '', '2026-01-15', '202601'],
            ['Voucher', '1000', '100.00', '', '', '2026-01-15', '202601'],
            ['Voucher', '4000', '', '100.00', '', '2026-01-15', '202601'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['created'], 1)

    def test_upload_preserves_line_order(self):
        excel = self._make_excel([
            ['Ordered', '1000', '100.00', '', 'First', '2026-01-15', '202601'],
            ['Ordered', '4000', '', '100.00', '', '2026-01-15', '202601'],
        ])
        resp = self.client.post(self.url, {'file': excel}, format='multipart')
        self.assertEqual(resp.status_code, 200)
        voucher = JournalVoucher.objects.first()
        entries = list(voucher.entries.all())
        self.assertEqual(entries[0].description, 'First')
