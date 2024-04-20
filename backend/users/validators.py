from django.core.exceptions import ValidationError


def check_me_name(value):
    if value == 'me':
        raise ValidationError('This username is forbidden!')
