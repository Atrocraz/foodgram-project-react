from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from users.validators import check_me_name


class FoodgramUser(AbstractUser):
    """Модель пользователя.

    Содержит дополнительные поля электронной почты, юзернейма, имени
    и фамилии пользователя.
    """

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    email = models.EmailField('Электронная почта',
                              max_length=settings.EMAIL_MAX_LEN,
                              unique=True)
    username = models.CharField(
        'Никнейм пользователя',
        unique=True,
        max_length=settings.USERNAME_MAX_LEN,
        help_text=(f'Обязательное. {settings.USERNAME_MAX_LEN} знаков или '
                   'менее. Допустимы буквы, цифры и @/./+/-/_.'),
        validators=(RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message='Использованы запрещённые символы!'), check_me_name)
    )
    first_name = models.CharField('Имя',
                                  max_length=settings.FIRST_NAME_MAX_LEN,
                                  blank=False)
    last_name = models.CharField('Фамилия',
                                 max_length=settings.SECOND_NAME_MAX_LEN,
                                 blank=False)

    class Meta:
        """Класс Meta модели."""

        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Строковое представление модели."""
        return f'Пользователь {self.username}'


class Follow(models.Model):
    """Модель подписки.

    Содержит поля пользователя и пользователя, на которого подписываются.
    """

    user = models.ForeignKey(FoodgramUser,
                             on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='follows')
    following = models.ForeignKey(FoodgramUser,
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  verbose_name='Подписка',
                                  related_name='following')

    class Meta:
        """Класс Meta модели."""

        ordering = ('user',)
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'following'],
                                    name='unique_user_following')
        ]

    def __str__(self):
        """Строковое представление модели."""
        return f'Пользователь {self.user} подписан на {self.following}'
