from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from users.models import Follow

User = get_user_model()


@admin.register(User)
class UserAdmin(UserAdmin):
    """Администрирование пользователей."""

    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
    )
    list_filter = ('username', 'email',)
    search_fields = ('username', 'email',)
    ordering = ('username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Администрирование подписок."""

    list_display = (
        'user',
        'following',
    )
    list_filter = ('user', 'following',)
    search_fields = ('user__username', 'following__username',)
