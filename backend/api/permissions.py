from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    '''Кастомный класс прав доступа.

    Блокирует доступ к всем запросам, кроме SAFE_METHODS
    для неавторизованных пользователей.

    Блокирует доступ к изменению записи в базе данных для всех,
    кроме автора записи.
    '''

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return request.user.is_authenticated
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'destroy']:
            return obj.author == request.user
        else:
            return True
