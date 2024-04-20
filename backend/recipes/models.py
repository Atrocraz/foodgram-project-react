from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models

from .validators import check_hex_code

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=settings.TAG_NAME_MAX_LEN,
                            verbose_name='Название',
                            blank=False)
    color = models.CharField(max_length=7,
                             unique=True,
                             verbose_name='Цветовой код',
                             validators=(check_hex_code, ))
    slug = models.SlugField(max_length=settings.TAG_SLUG_MAX_LEN,
                            unique=True,
                            verbose_name='Слаг',
                            validators=(RegexValidator(
                                regex=r'^[-a-zA-Z0-9_]+$',
                                message='Forbidden symbol in username!'), ))

    class Meta:
        """Meta class for Tag model."""

        default_related_name = 'tags'
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name}'


class Ingredient(models.Model):
    name = models.CharField(max_length=settings.INGREDIENT_NAME_MAX_LEN,
                            verbose_name='Название')

    measurement_unit = models.CharField(
        max_length=settings.MEAS_UNIT_NAME_MAX_LEN,
        verbose_name='Единица измерения')

    class Meta:
        """Meta class for Ingredient model."""

        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField(max_length=settings.RECIPE_NAME_MAX_LEN)
    image = models.TextField(verbose_name='Изображение блюда')
    text = models.TextField(verbose_name='Текстовое описание')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         through_fields=('recipe',
                                                         'ingredient'),
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления')

    class Meta:
        """Meta class for Recipe model."""

        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='ingredients')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipes')
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        """Meta class for Recipe model."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'
