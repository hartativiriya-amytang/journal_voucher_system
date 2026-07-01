from accounting_period.models import AccountingPeriod
from accounting_period.serializers import AccountingPeriodSerializer
from common.views import BaseViewSet


class AccountingPeriodViewSet(BaseViewSet):
    queryset = AccountingPeriod.objects.all()
    serializer_class = AccountingPeriodSerializer
    search_fields = ['code', 'name']
