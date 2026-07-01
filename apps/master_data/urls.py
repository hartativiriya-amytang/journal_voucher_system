from rest_framework.routers import DefaultRouter
from master_data.views import CompanyViewSet, BranchViewSet, CurrencyViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'currencies', CurrencyViewSet, basename='currency')

urlpatterns = router.urls
