from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    USERNAME_FIELD = 'email'
    # Строка ниже возможно багует всё
    REQUIRED_FIELDS = ['name', 'surname']
    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        verbose_name='Электронная почта'
    )
    name = models.CharField(
        max_length=254,
        blank=False,
        verbose_name='Имя')
    surname = models.CharField(
        max_length=254,
        blank=False,
        verbose_name='Фамилия')
