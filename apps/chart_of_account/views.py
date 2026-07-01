from chart_of_account.models import ChartOfAccount
from chart_of_account.serializers import ChartOfAccountSerializer
from common.views import BaseViewSet


class ChartOfAccountViewSet(BaseViewSet):
    queryset = ChartOfAccount.objects.all()
    serializer_class = ChartOfAccountSerializer
    search_fields = ['code', 'name']
