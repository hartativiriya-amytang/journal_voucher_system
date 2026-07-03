from rest_framework.routers import DefaultRouter
from journal_voucher.views import JournalVoucherViewSet

router = DefaultRouter()
router.register(r'', JournalVoucherViewSet, basename='journalvoucher')

urlpatterns = router.urls
