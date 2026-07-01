class AuditLogMixin:
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class SoftDeleteMixin:
    def delete_model(self, request, obj):
        obj.is_active = False
        obj.save()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)
