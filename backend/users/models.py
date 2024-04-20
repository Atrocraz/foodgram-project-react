from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .validators import check_me_name


class MyUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    email = models.EmailField('Электронная почта',
                              max_length=settings.EMAIL_MAX_LEN,
                              unique=True,
                              blank=False)
    username = models.CharField(
        'Никнейм пользователя',
        unique=True,
        max_length=settings.USERNAME_MAX_LEN,
        help_text=(f'Обязательное. {settings.USERNAME_MAX_LEN} знаков или '
                   f'менее. Допустимы буквы, цифры и @/./+/-/_.'),
        validators=(RegexValidator(regex=r'^[\w.@+-]+\Z',
                                   message='Forbidden symbol in username!'),
                    check_me_name),
    )
    first_name = models.CharField('Имя',
                                  max_length=settings.FIRST_NAME_MAX_LEN,
                                  blank=False)
    last_name = models.CharField('Фамилия',
                                 max_length=settings.SECOND_NAME_MAX_LEN,
                                 blank=False)

    @property
    def is_admin(self):
        return self.is_superuser


class Follow(models.Model):
    """
    Follow model class.

    Contains user and following fields.
    """

    user = models.ForeignKey(MyUser,
                             on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='follows')
    following = models.ForeignKey(MyUser,
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  verbose_name='Подписка',
                                  related_name='following')

    class Meta:
        """Meta class for Follow model."""

        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'following'],
                                    name='unique_user_following')
        ]

    def __str__(self):
        """Magic method for Follow model."""
        return f'Пользователь {self.user} подписан на {self.following}'
