from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from accounting_period.models import AccountingPeriod


class AccountingPeriodTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='PER-2026-01',
            name='January 2026',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

    def test_period_creation(self):
        self.assertEqual(str(self.period), '[PER-2026-01] January 2026')
        self.assertEqual(self.period.status, 'OPEN')

    def test_period_validation_start_before_end(self):
        with self.assertRaises(ValidationError):
            AccountingPeriod.objects.create(
                code='PER-INVALID',
                name='Invalid Period',
                start_date=date(2026, 2, 1),
                end_date=date(2026, 1, 1),
            )
