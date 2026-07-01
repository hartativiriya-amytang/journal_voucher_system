from django.contrib import admin
from chart_of_account.models import ChartOfAccount
from common.admin import BaseModelAdmin


@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(BaseModelAdmin):
    list_display = ['code', 'name', 'account_type', 'parent', 'normal_balance', 'is_active']
    list_filter = ['account_type', 'normal_balance', 'is_active']
    search_fields = ['code', 'name']
