from vendor.models import Vendor
from vendor.serializers import VendorSerializer
from common.views import BaseViewSet


class VendorViewSet(BaseViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    search_fields = ['code', 'name', 'email', 'tax_id']
