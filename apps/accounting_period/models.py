from django.db import models
from django.core.exceptions import ValidationError
from common.constants import PeriodStatus
from common.models import BaseModel


class AccountingPeriod(BaseModel):
    code = models.CharField(max_length=20, unique=True, verbose_name='Period Code')
    name = models.CharField(max_length=255, verbose_name='Period Name')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=PeriodStatus.choices, default=PeriodStatus.OPEN)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Accounting Period'
        verbose_name_plural = 'Accounting Periods'

    def __str__(self):
        return f'[{self.code}] {self.name}'

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date must be before end date.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
