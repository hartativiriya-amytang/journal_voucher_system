from django.contrib import admin
from journal_voucher.models import JournalVoucher, JournalEntry
from common.admin import BaseModelAdmin


class JournalEntryInline(admin.TabularInline):
    model = JournalEntry
    extra = 1
    fields = ['account', 'debit', 'credit', 'description', 'line_order']


@admin.register(JournalVoucher)
class JournalVoucherAdmin(BaseModelAdmin):
    list_display = [
        'voucher_number', 'transaction_date', 'accounting_period',
        'vendor', 'status', 'total_debit', 'total_credit', 'created_at',
    ]
    list_filter = ['status', 'accounting_period']
    search_fields = ['voucher_number', 'description', 'bl_number', 'invoice_number']
    readonly_fields = ['voucher_number', 'total_debit', 'total_credit', 'created_by', 'created_at', 'updated_at']
    inlines = [JournalEntryInline]
    date_hierarchy = 'transaction_date'


@admin.register(JournalEntry)
class JournalEntryAdmin(BaseModelAdmin):
    list_display = ['voucher', 'account', 'debit', 'credit', 'description', 'line_order']
    list_filter = ['account']
    search_fields = ['voucher__voucher_number', 'account__code', 'account__name', 'description']
