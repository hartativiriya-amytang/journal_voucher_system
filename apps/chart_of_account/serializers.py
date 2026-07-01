from rest_framework import serializers
from chart_of_account.models import ChartOfAccount
from common.serializers import BaseModelSerializer


class ChartOfAccountSerializer(BaseModelSerializer):
    parent_code = serializers.CharField(source='parent.code', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = ChartOfAccount
        fields = '__all__'

    def get_children_count(self, obj):
        return obj.children.count()
