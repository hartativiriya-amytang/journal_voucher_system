from decimal import Decimal
from django.core.exceptions import ValidationError
from common.constants import PeriodStatus, Status


def validate_debit_credit_balance(entries):
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    for entry in entries:
        if isinstance(entry, dict):
            total_debit += entry.get('debit', 0) or 0
            total_credit += entry.get('credit', 0) or 0
        else:
            total_debit += entry.debit or 0
            total_credit += entry.credit or 0
    if total_debit != total_credit:
        raise ValidationError(
            f'Total debit ({total_debit}) must equal total credit ({total_credit}).'
        )
    return total_debit, total_credit


def validate_period_open(period):
    if period.status != PeriodStatus.OPEN:
        raise ValidationError(
            f'Period {period.code} is {period.status}. Only open periods can accept vouchers.'
        )


def validate_account_active(account):
    if account.is_active != Status.ACTIVE:
        raise ValidationError(
            f'Account {account.code} - {account.name} is not active.'
        )
