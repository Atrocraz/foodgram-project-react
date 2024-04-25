from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .validators import check_me_name


class MyUser(AbstractUser):
    '''Кастомная модель пользователя.

    Содержит дополнительные поля электронной почты, юзернейма, имени
    и фамилии пользователя.'''

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
        validators=(RegexValidator(
                        regex=r'^[\w.@+-]+\Z',
                        message='Использованы запрещённые символы!'),
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
        'Метод для проверки наличия прав суперпользователя.'
        return self.is_superuser


class Follow(models.Model):
    '''
    Модель подписки.

    Содержит поля пользователя и пользователя, на которого подписываются.
    '''
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
        'Класс Meta модели.'

        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'following'],
                                    name='unique_user_following')
        ]

    def __str__(self):
        'Магический метод модели.'
        return f'Пользователь {self.user} подписан на {self.following}'
