from rest_framework import serializers
from accounting_period.models import AccountingPeriod
from common.serializers import BaseModelSerializer


class AccountingPeriodSerializer(BaseModelSerializer):
    class Meta:
        model = AccountingPeriod
        fields = '__all__'
