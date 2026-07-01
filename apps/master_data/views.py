from rest_framework import viewsets
from master_data.models import Company, Branch, Currency
from master_data.serializers import CompanySerializer, BranchSerializer, CurrencySerializer
from common.views import BaseViewSet


class CompanyViewSet(BaseViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    search_fields = ['code', 'name', 'email']


class BranchViewSet(BaseViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    search_fields = ['code', 'name']


class CurrencyViewSet(BaseViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    search_fields = ['code', 'name']
