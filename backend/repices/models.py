from django.contrib.auth import get_user_model
from django.db import models

from .validators import check_hex_code, check_positive

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')
    color = models.CharField(
        max_length=7,
        verbose_name='Цветовой код',
        validators=(check_hex_code,))
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        """Meta class for Tag model."""

        default_related_name = 'tags'
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'
        # ordering = ('pub_date',)

    def __str__(self):
        return f'{self.name}'


class MeasureTypes(models.Model):
    measure = models.CharField(max_length=12)

    class Meta:
        """Meta class for MeasureTypes model."""

        default_related_name = 'measures'
        verbose_name = 'ед. измерения'
        verbose_name_plural = 'Ед. измерения'
        # ordering = ('pub_date',)

    def __str__(self):
        return f'{self.measure}'


class Ingredient(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')
    amount = models.SmallIntegerField(
        verbose_name='Количество',
        validators=(check_positive,)
    )
    measure_type = models.ForeignKey(
        MeasureTypes,
        on_delete=models.CASCADE
    )

    class Meta:
        """Meta class for Ingredient model."""

        default_related_name = 'ingredients'
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        # ordering = ('pub_date',)

    def __str__(self):
        return f'{self.name}'


class Repice(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(max_length=64)
    image = models.ImageField(
        upload_to='images/',
        null=True, blank=True,
        verbose_name='Картинка'
    )
    description = models.TextField(verbose_name='Текстовое описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientsRepice')
    tags = models.ManyToManyField(
        Tag, through='TagsRepice')
    cooking_time = models.SmallIntegerField(
        verbose_name='Время приготовления',
        validators=(check_positive,)
        )

    class Meta:
        """Meta class for Repice model."""

        default_related_name = 'repices'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        # ordering = ('pub_date',)

    def __str__(self):
        return f'{self.name}'


class IngredientsRepice(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    repice = models.ForeignKey(Repice, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.ingredient} {self.repice}'


class TagsRepice(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    repice = models.ForeignKey(Repice, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.tag} {self.repice}'


class Follow(models.Model):
    """
    Follow model class.

    Contains user and following fields.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='follows'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Подписка',
        related_name='following'
    )

    class Meta:
        """Meta class for Follow model."""

        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            )
        ]

    def __str__(self):
        """Magic method for Follow model."""
        return f'Пользователь {self.user} подписан на {self.following}'
