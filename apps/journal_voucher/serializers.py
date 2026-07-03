from rest_framework import serializers
from journal_voucher.models import JournalVoucher, JournalEntry
from common.serializers import BaseModelSerializer


class JournalEntrySerializer(BaseModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'voucher', 'account', 'account_code', 'account_name',
            'debit', 'credit', 'description', 'line_order',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['voucher']


class JournalEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = ['account', 'debit', 'credit', 'description', 'line_order']


class JournalVoucherListSerializer(BaseModelSerializer):
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = JournalVoucher
        fields = [
            'id', 'voucher_number', 'accounting_period', 'accounting_period_name',
            'transaction_date', 'description', 'vendor', 'vendor_name',
            'status', 'total_debit', 'total_credit', 'created_by_username',
            'created_at', 'updated_at',
        ]


class JournalVoucherSerializer(BaseModelSerializer):
    entries = JournalEntryCreateSerializer(many=True)
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = JournalVoucher
        fields = [
            'id', 'voucher_number', 'accounting_period', 'accounting_period_name',
            'transaction_date', 'description', 'bl_number', 'invoice_number',
            'vendor', 'vendor_name', 'status', 'total_debit', 'total_credit',
            'created_by', 'created_by_username', 'entries',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['voucher_number', 'total_debit', 'total_credit', 'status', 'created_by']

    def validate_entries(self, value):
        if not value:
            raise serializers.ValidationError('At least one journal entry is required.')
        for i, entry in enumerate(value):
            debit = entry.get('debit', 0) or 0
            credit = entry.get('credit', 0) or 0
            if debit > 0 and credit > 0:
                raise serializers.ValidationError(
                    f'Entry line {i + 1}: cannot have both debit and credit values.'
                )
            if debit == 0 and credit == 0:
                raise serializers.ValidationError(
                    f'Entry line {i + 1}: must have either debit or credit value.'
                )
        return value

    def _update_totals(self, voucher):
        entries = voucher.entries.all()
        voucher.total_debit = sum(e.debit for e in entries)
        voucher.total_credit = sum(e.credit for e in entries)
        voucher.save(update_fields=['total_debit', 'total_credit'])

    def create(self, validated_data):
        entries_data = validated_data.pop('entries')
        validated_data['created_by'] = self.context['request'].user
        voucher = JournalVoucher.objects.create(**validated_data)
        for i, entry_data in enumerate(entries_data):
            JournalEntry.objects.create(voucher=voucher, line_order=i, **entry_data)
        self._update_totals(voucher)
        return voucher

    def update(self, instance, validated_data):
        entries_data = validated_data.pop('entries', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if entries_data is not None:
            instance.entries.all().delete()
            for i, entry_data in enumerate(entries_data):
                JournalEntry.objects.create(voucher=instance, line_order=i, **entry_data)
        self._update_totals(instance)
        return instance


class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
