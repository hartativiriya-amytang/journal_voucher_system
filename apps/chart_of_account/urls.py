from rest_framework.routers import DefaultRouter
from chart_of_account.views import ChartOfAccountViewSet

router = DefaultRouter()
router.register(r'', ChartOfAccountViewSet, basename='chartofaccount')

urlpatterns = router.urls
