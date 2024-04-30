from django.core.exceptions import ValidationError


def check_me_name(value):
    """Валидатор для проверки на имя пользователя me при регистрации."""
    if value == 'me':
        raise ValidationError('Это имя запрещено использовать!')
