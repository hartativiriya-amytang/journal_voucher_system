from django.db import models
from common.constants import Status
from common.models import BaseModel


class Company(BaseModel):
    code = models.CharField(max_length=20, unique=True, verbose_name='Company Code')
    name = models.CharField(max_length=255, verbose_name='Company Name')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['code']

    def __str__(self):
        return f'[{self.code}] {self.name}'


class Branch(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    code = models.CharField(max_length=20, verbose_name='Branch Code')
    name = models.CharField(max_length=255, verbose_name='Branch Name')
    address = models.TextField(blank=True)
    is_active = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        unique_together = ['company', 'code']
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['company__code', 'code']

    def __str__(self):
        return f'[{self.company.code}-{self.code}] {self.name}'


class Currency(BaseModel):
    code = models.CharField(max_length=10, unique=True, verbose_name='Currency Code')
    name = models.CharField(max_length=100, verbose_name='Currency Name')
    symbol = models.CharField(max_length=5, blank=True)
    is_active = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
        ordering = ['code']

    def __str__(self):
        return f'[{self.code}] {self.name}'
