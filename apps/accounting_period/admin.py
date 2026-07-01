from django.contrib import admin
from accounting_period.models import AccountingPeriod
from common.admin import BaseModelAdmin


@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(BaseModelAdmin):
    list_display = ['code', 'name', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['code', 'name']
    date_hierarchy = 'start_date'
