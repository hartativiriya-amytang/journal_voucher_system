from django.test import TestCase
from django.contrib.auth.models import User


class CommonTests(TestCase):
    def test_base_model_abstract(self):
        # BaseModel should be abstract — test passes if no import error
        from common.models import BaseModel
        self.assertTrue(BaseModel._meta.abstract)

    def test_constants_choices(self):
        from common.constants import Status, PeriodStatus, AccountType, NormalBalance, VoucherStatus
        self.assertTrue(len(Status.choices) > 0)
        self.assertTrue(len(PeriodStatus.choices) > 0)
        self.assertTrue(len(AccountType.choices) > 0)
        self.assertTrue(len(NormalBalance.choices) > 0)
        self.assertTrue(len(VoucherStatus.choices) > 0)
