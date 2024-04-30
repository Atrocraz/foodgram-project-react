from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Кастомный класс прав доступа.

    Блокирует доступ к всем запросам, кроме SAFE_METHODS
    для неавторизованных пользователей.

    Блокирует доступ к изменению записи в базе данных для всех,
    кроме автора записи.
    """

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS or request.user == obj.author)
