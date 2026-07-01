from django.contrib import admin
from vendor.models import Vendor
from common.admin import BaseModelAdmin


@admin.register(Vendor)
class VendorAdmin(BaseModelAdmin):
    list_display = ['code', 'name', 'phone', 'email', 'tax_id', 'credit_limit', 'is_active']
    list_filter = ['is_active', 'payment_terms']
    search_fields = ['code', 'name', 'email', 'tax_id']
