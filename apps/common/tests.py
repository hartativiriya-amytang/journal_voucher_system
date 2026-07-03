from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework import serializers


class CommonModelsTests(TestCase):
    def test_base_model_is_abstract(self):
        from common.models import BaseModel
        self.assertTrue(BaseModel._meta.abstract)

    def test_base_model_creates_timestamps(self):
        from master_data.models import Company
        obj = Company.objects.create(code='TS', name='Timestamp Test')
        self.assertIsInstance(obj.created_at, datetime)
        self.assertIsInstance(obj.updated_at, datetime)


class CommonConstantsTests(TestCase):
    def test_all_choices_have_values(self):
        from common.constants import Status, PeriodStatus, AccountType, NormalBalance, VoucherStatus
        self.assertEqual(Status.ACTIVE, 'ACTIVE')
        self.assertEqual(Status.INACTIVE, 'INACTIVE')
        self.assertEqual(PeriodStatus.OPEN, 'OPEN')
        self.assertEqual(PeriodStatus.CLOSED, 'CLOSED')
        self.assertEqual(AccountType.ASSET, 'ASSET')
        self.assertEqual(AccountType.LIABILITY, 'LIABILITY')
        self.assertEqual(AccountType.EQUITY, 'EQUITY')
        self.assertEqual(AccountType.REVENUE, 'REVENUE')
        self.assertEqual(AccountType.EXPENSE, 'EXPENSE')
        self.assertEqual(NormalBalance.DEBIT, 'DEBIT')
        self.assertEqual(NormalBalance.CREDIT, 'CREDIT')
        self.assertEqual(VoucherStatus.DRAFT, 'DRAFT')
        self.assertEqual(VoucherStatus.VALIDATED, 'VALIDATED')
        self.assertEqual(VoucherStatus.POSTED, 'POSTED')
        self.assertEqual(VoucherStatus.VOID, 'VOID')


class CommonSerializerTests(TestCase):
    def test_base_serializer_has_read_only_timestamps(self):
        from common.serializers import BaseModelSerializer
        from master_data.models import Company
        from master_data.serializers import CompanySerializer

        self.assertTrue(issubclass(CompanySerializer, BaseModelSerializer))
        fields = CompanySerializer().get_fields()
        self.assertTrue(fields['created_at'].read_only)
        self.assertTrue(fields['updated_at'].read_only)


class CommonViewSetTests(TestCase):
    def test_base_viewset_has_correct_permissions(self):
        from common.views import BaseViewSet
        from rest_framework.permissions import IsAuthenticated
        self.assertIn(IsAuthenticated, BaseViewSet.permission_classes)

    def test_base_viewset_has_filter_backends(self):
        from common.views import BaseViewSet
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters
        self.assertIn(DjangoFilterBackend, BaseViewSet.filter_backends)
        self.assertIn(filters.SearchFilter, BaseViewSet.filter_backends)
        self.assertIn(filters.OrderingFilter, BaseViewSet.filter_backends)

    def test_base_viewset_default_ordering(self):
        from common.views import BaseViewSet
        self.assertEqual(BaseViewSet.ordering, ['-created_at'])


class PermissionTests(TestCase):
    def test_is_active_passes_for_active_user(self):
        from common.permissions import IsActive
        request = APIRequestFactory().get('/')
        request.user = User(is_active=True)
        self.assertTrue(IsActive().has_permission(request, None))

    def test_is_active_fails_for_inactive_user(self):
        from common.permissions import IsActive
        request = APIRequestFactory().get('/')
        request.user = User(is_active=False)
        self.assertFalse(IsActive().has_permission(request, None))

    def test_read_only_allows_safe_methods(self):
        from common.permissions import ReadOnly
        for method in ['GET', 'HEAD', 'OPTIONS']:
            request = APIRequestFactory().generic(method, '/')
            self.assertTrue(ReadOnly().has_permission(request, None))

    def test_read_only_blocks_write_methods(self):
        from common.permissions import ReadOnly
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            request = APIRequestFactory().generic(method, '/')
            self.assertFalse(ReadOnly().has_permission(request, None))


class MixinTests(TestCase):
    def test_audit_log_mixin_behavior_with_valid_super(self):
        from common.mixins import AuditLogMixin

        recorded = []

        class FakeModelAdmin:
            def save_model(self, request, obj, form, change):
                recorded.append(('super_called', obj.created_by if hasattr(obj, 'created_by') else None,
                                 obj.updated_by if hasattr(obj, 'updated_by') else None))

        class TestAdmin(AuditLogMixin, FakeModelAdmin):
            pass

        request = type('Req', (), {'user': User(username='tester')})()
        obj = type('Obj', (), {'pk': None})

        admin = TestAdmin()
        admin.save_model(request, obj, None, change=False)
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0][1], request.user)  # created_by set before super
        self.assertEqual(recorded[0][2], request.user)  # updated_by set before super

    def test_audit_log_mixin_does_not_set_created_by_on_change(self):
        from common.mixins import AuditLogMixin

        recorded = []

        class FakeModelAdmin:
            def save_model(self, request, obj, form, change):
                recorded.append(('super_called', hasattr(obj, 'created_by'),
                                 obj.updated_by if hasattr(obj, 'updated_by') else None))

        class TestAdmin(AuditLogMixin, FakeModelAdmin):
            pass

        request = type('Req', (), {'user': User(username='updater')})()
        obj = type('Obj', (), {'pk': 1})

        admin = TestAdmin()
        admin.save_model(request, obj, None, change=True)
        self.assertEqual(len(recorded), 1)
        self.assertFalse(recorded[0][1])  # created_by NOT set on change
        self.assertEqual(recorded[0][2], request.user)  # updated_by still set
