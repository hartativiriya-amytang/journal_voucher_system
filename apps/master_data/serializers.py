from rest_framework import serializers
from master_data.models import Company, Branch, Currency
from common.serializers import BaseModelSerializer


class CompanySerializer(BaseModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class BranchSerializer(BaseModelSerializer):
    company_code = serializers.CharField(source='company.code', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Branch
        fields = '__all__'


class CurrencySerializer(BaseModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'
