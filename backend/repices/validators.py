import re

from django.core.exceptions import ValidationError


def check_hex_code(value):
    if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValidationError(
            'Неверный формат цветового кода'
        )


def check_positive(value):
    if value <= 0:
        raise ValidationError(
            'Значение должно быть положительным'
        )