from django.contrib import admin
from master_data.models import Company, Branch, Currency
from common.admin import BaseModelAdmin


@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    list_display = ['code', 'name', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'email']


@admin.register(Branch)
class BranchAdmin(BaseModelAdmin):
    list_display = ['code', 'name', 'company', 'is_active', 'created_at']
    list_filter = ['is_active', 'company']
    search_fields = ['code', 'name']


@admin.register(Currency)
class CurrencyAdmin(BaseModelAdmin):
    list_display = ['code', 'name', 'symbol', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
