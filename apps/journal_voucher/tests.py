from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
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
            code='1000', name='Cash', account_type='ASSET',
            normal_balance='DEBIT',
        )
        self.account2 = ChartOfAccount.objects.create(
            code='4000', name='Revenue', account_type='REVENUE',
            normal_balance='CREDIT',
        )
        self.vendor = Vendor.objects.create(
            code='V001', name='Test Vendor',
        )
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')

    def test_create_voucher_generates_number(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period,
            transaction_date=date(2026, 1, 15),
            description='Test voucher',
        )
        self.assertTrue(voucher.voucher_number.startswith('JV-'))
        self.assertEqual(voucher.status, VoucherStatus.DRAFT)
        self.assertEqual(voucher.total_debit, 0)
        self.assertEqual(voucher.total_credit, 0)

    def test_transaction_date_within_period(self):
        with self.assertRaises(ValidationError):
            JournalVoucher.objects.create(
                accounting_period=self.period,
                transaction_date=date(2026, 2, 1),
                description='Out of period',
            )

    def test_voucher_str(self):
        voucher = JournalVoucher.objects.create(
            accounting_period=self.period,
            transaction_date=date(2026, 1, 15),
            description='Test voucher',
        )
        self.assertIn(voucher.voucher_number, str(voucher))
        self.assertIn('Test voucher', str(voucher))


class JournalEntryModelTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='202601', name='Jan 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        self.account = ChartOfAccount.objects.create(
            code='1000', name='Cash', account_type='ASSET',
            normal_balance='DEBIT',
        )
        self.voucher = JournalVoucher.objects.create(
            accounting_period=self.period,
            transaction_date=date(2026, 1, 15),
            description='Test voucher',
        )

    def test_entry_requires_debit_or_credit(self):
        with self.assertRaises(ValidationError):
            JournalEntry.objects.create(
                voucher=self.voucher, account=self.account,
                debit=0, credit=0,
            )

    def test_entry_cannot_have_both_debit_and_credit(self):
        with self.assertRaises(ValidationError):
            JournalEntry.objects.create(
                voucher=self.voucher, account=self.account,
                debit=100, credit=100,
            )

    def test_valid_entry_debit(self):
        entry = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=Decimal('100.00'), credit=0,
        )
        self.assertEqual(entry.debit, Decimal('100.00'))
        self.assertEqual(entry.credit, 0)

    def test_valid_entry_credit(self):
        entry = JournalEntry.objects.create(
            voucher=self.voucher, account=self.account,
            debit=0, credit=Decimal('100.00'),
        )
        self.assertEqual(entry.debit, 0)
        self.assertEqual(entry.credit, Decimal('100.00'))


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

    def test_validate_period_open(self):
        validate_period_open(self.period)  # should not raise

    def test_validate_period_closed(self):
        self.period.status = PeriodStatus.CLOSED
        with self.assertRaises(ValidationError):
            validate_period_open(self.period)

    def test_validate_account_active(self):
        validate_account_active(self.active_account)

    def test_validate_account_inactive(self):
        with self.assertRaises(ValidationError):
            validate_account_active(self.inactive_account)

    def test_validate_debit_credit_with_dicts(self):
        entries = [
            {'debit': Decimal('200'), 'credit': Decimal('0')},
            {'debit': Decimal('0'), 'credit': Decimal('200')},
        ]
        total_d, total_c = validate_debit_credit_balance(entries)
        self.assertEqual(total_d, Decimal('200'))
        self.assertEqual(total_c, Decimal('200'))
