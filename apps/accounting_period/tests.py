from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from accounting_period.models import AccountingPeriod
from common.constants import PeriodStatus


class AccountingPeriodModelTests(TestCase):
    def setUp(self):
        self.period = AccountingPeriod.objects.create(
            code='PER-2026-01',
            name='January 2026',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

    def test_str(self):
        self.assertEqual(str(self.period), '[PER-2026-01] January 2026')

    def test_default_status_is_open(self):
        self.assertEqual(self.period.status, PeriodStatus.OPEN)

    def test_start_before_end_validates(self):
        with self.assertRaises(ValidationError):
            AccountingPeriod.objects.create(
                code='PER-INVALID',
                name='Invalid Period',
                start_date=date(2026, 2, 1),
                end_date=date(2026, 1, 1),
            )

    def test_start_equal_end_is_valid(self):
        period = AccountingPeriod.objects.create(
            code='PER-SINGLE',
            name='Single Day',
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 1),
        )
        self.assertEqual(period.start_date, period.end_date)

    def test_notes_default_blank(self):
        self.assertEqual(self.period.notes, '')

    def test_can_update_status(self):
        self.period.status = PeriodStatus.CLOSED
        self.period.save()
        self.period.refresh_from_db()
        self.assertEqual(self.period.status, PeriodStatus.CLOSED)

    def test_ordering_by_start_date_desc(self):
        AccountingPeriod.objects.create(
            code='P-2025', name='2025',
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        AccountingPeriod.objects.create(
            code='P-2027', name='2027',
            start_date=date(2027, 1, 1), end_date=date(2027, 12, 31),
        )
        periods = list(AccountingPeriod.objects.all())
        self.assertEqual(periods[0].code, 'P-2027')
        self.assertEqual(periods[1].code, 'PER-2026-01')
        self.assertEqual(periods[2].code, 'P-2025')

    def test_unique_code_enforced(self):
        with self.assertRaises(Exception):
            AccountingPeriod.objects.create(
                code='PER-2026-01',
                name='Duplicate',
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
            )


class AccountingPeriodAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password')
        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/accounting-periods/'

    def test_list_periods(self):
        AccountingPeriod.objects.create(
            code='P1', name='Period 1',
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        AccountingPeriod.objects.create(
            code='P2', name='Period 2',
            start_date=date(2026, 2, 1), end_date=date(2026, 2, 28),
        )
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 2)

    def test_create_period(self):
        resp = self.client.post(self.list_url, {
            'code': 'PER-2026-03',
            'name': 'March 2026',
            'start_date': '2026-03-01',
            'end_date': '2026-03-31',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['code'], 'PER-2026-03')

    def test_create_period_invalid_dates_returns_400(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.client.post(self.list_url, {
                'code': 'PER-INVALID',
                'name': 'Bad',
                'start_date': '2026-03-31',
                'end_date': '2026-03-01',
            }, format='json')

    def test_retrieve_period(self):
        p = AccountingPeriod.objects.create(
            code='PER-RET', name='Retrieve',
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 30),
        )
        resp = self.client.get(f'{self.list_url}{p.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['code'], 'PER-RET')

    def test_update_period(self):
        p = AccountingPeriod.objects.create(
            code='PER-UPD', name='Old',
            start_date=date(2026, 5, 1), end_date=date(2026, 5, 31),
        )
        resp = self.client.patch(f'{self.list_url}{p.id}/', {'name': 'New Name'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'New Name')

    def test_delete_period(self):
        p = AccountingPeriod.objects.create(
            code='PER-DEL', name='Delete',
            start_date=date(2026, 6, 1), end_date=date(2026, 6, 30),
        )
        resp = self.client.delete(f'{self.list_url}{p.id}/')
        self.assertEqual(resp.status_code, 204)

    def test_search_periods(self):
        AccountingPeriod.objects.create(
            code='FY-2026', name='Fiscal Year 2026',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        resp = self.client.get(f'{self.list_url}?search=Fiscal')
        self.assertEqual(len(resp.data['results']), 1)

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 403)

    def test_timestamps_in_response(self):
        p = AccountingPeriod.objects.create(
            code='PER-TS', name='Timestamps',
            start_date=date(2026, 7, 1), end_date=date(2026, 7, 31),
        )
        resp = self.client.get(f'{self.list_url}{p.id}/')
        self.assertIn('created_at', resp.data)
        self.assertIn('updated_at', resp.data)
