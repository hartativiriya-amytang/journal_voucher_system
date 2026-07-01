from rest_framework import serializers
from vendor.models import Vendor
from common.serializers import BaseModelSerializer


class VendorSerializer(BaseModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
