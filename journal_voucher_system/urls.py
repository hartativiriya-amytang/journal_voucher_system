from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('common.urls')),
    path('api/master-data/', include('master_data.urls')),
    path('api/accounting-periods/', include('accounting_period.urls')),
    path('api/chart-of-accounts/', include('chart_of_account.urls')),
    path('api/vendors/', include('vendor.urls')),
    path('api/journal-vouchers/', include('journal_voucher.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
