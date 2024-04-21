from rest_framework.permissions import BasePermission


class AdvancedPermission(BasePermission):

    def has_permission(self, request, view):
        if view.action in ['create', 'update', 'partial_update', 'destroy']:
            return request.user.is_authenticated
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'destroy']:
            return obj.author == request.user
        else:
            return True
