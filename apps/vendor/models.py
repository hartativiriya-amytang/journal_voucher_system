from django.db import models
from common.constants import Status
from common.models import BaseModel


class Vendor(BaseModel):
    code = models.CharField(max_length=20, unique=True, verbose_name='Vendor Code')
    name = models.CharField(max_length=255, verbose_name='Vendor Name')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='Tax ID')
    bank_account = models.CharField(max_length=50, blank=True, verbose_name='Bank Account')
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payment_terms = models.CharField(max_length=100, blank=True)
    is_active = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['code']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'

    def __str__(self):
        return f'[{self.code}] {self.name}'
