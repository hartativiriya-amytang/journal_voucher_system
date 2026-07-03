from django.db import models
from django.core.exceptions import ValidationError
from common.constants import VoucherStatus
from common.models import BaseModel


class JournalVoucher(BaseModel):
    voucher_number = models.CharField(max_length=50, unique=True, verbose_name='Voucher Number')
    accounting_period = models.ForeignKey(
        'accounting_period.AccountingPeriod',
        on_delete=models.PROTECT,
        related_name='vouchers',
        verbose_name='Accounting Period'
    )
    transaction_date = models.DateField(verbose_name='Transaction Date')
    description = models.TextField(verbose_name='Description')
    bl_number = models.CharField(max_length=100, blank=True, verbose_name='BL Number')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='Invoice Number')
    vendor = models.ForeignKey(
        'vendor.Vendor',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='vouchers',
        verbose_name='Vendor'
    )
    status = models.CharField(
        max_length=10, choices=VoucherStatus.choices, default=VoucherStatus.DRAFT
    )
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vouchers'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Journal Voucher'
        verbose_name_plural = 'Journal Vouchers'

    def __str__(self):
        return f'[{self.voucher_number}] {self.description[:50]}'

    def clean(self):
        if self.accounting_period_id and self.transaction_date:
            period = self.accounting_period
            if self.transaction_date < period.start_date or self.transaction_date > period.end_date:
                raise ValidationError(
                    f'Transaction date must be within period {period.code} '
                    f'({period.start_date} to {period.end_date}).'
                )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.voucher_number:
            self.voucher_number = self._generate_voucher_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_voucher_number():
        from django.utils.timezone import localdate
        today = localdate()
        prefix = f'JV-{today.strftime("%Y%m%d")}-'
        last = JournalVoucher.objects.filter(
            voucher_number__startswith=prefix
        ).order_by('voucher_number').last()
        if last:
            last_num = int(last.voucher_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f'{prefix}{new_num:04d}'


class JournalEntry(BaseModel):
    voucher = models.ForeignKey(
        JournalVoucher, on_delete=models.CASCADE,
        related_name='entries',
        verbose_name='Voucher'
    )
    account = models.ForeignKey(
        'chart_of_account.ChartOfAccount',
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name='Account'
    )
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)
    line_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['line_order']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f'{self.voucher.voucher_number} - {self.account.code}: {self.debit}/{self.credit}'

    def clean(self):
        if self.debit > 0 and self.credit > 0:
            raise ValidationError('An entry cannot have both debit and credit values.')
        if self.debit == 0 and self.credit == 0:
            raise ValidationError('An entry must have either debit or credit value.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
