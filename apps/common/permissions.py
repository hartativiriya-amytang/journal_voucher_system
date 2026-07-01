from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsActive(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_active


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
