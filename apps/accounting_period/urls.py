from rest_framework.routers import DefaultRouter
from accounting_period.views import AccountingPeriodViewSet

router = DefaultRouter()
router.register(r'', AccountingPeriodViewSet, basename='accountingperiod')

urlpatterns = router.urls
