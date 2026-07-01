from django.db import models
from common.constants import AccountType, NormalBalance, Status
from common.models import BaseModel


class ChartOfAccount(BaseModel):
    code = models.CharField(max_length=20, unique=True, verbose_name='Account Code')
    name = models.CharField(max_length=255, verbose_name='Account Name')
    account_type = models.CharField(max_length=10, choices=AccountType.choices)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name='Parent Account'
    )
    normal_balance = models.CharField(max_length=6, choices=NormalBalance.choices)
    is_active = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Chart of Account'
        verbose_name_plural = 'Chart of Accounts'
        ordering = ['code']

    def __str__(self):
        return f'[{self.code}] {self.name}'
