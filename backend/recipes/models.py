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
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_unit_list'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField(max_length=settings.RECIPE_NAME_MAX_LEN)
    image = models.ImageField(
        "Ссылка на изображение",
        upload_to="recipes/images/"
    )
    text = models.TextField(verbose_name='Текстовое описание')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         through_fields=('recipe',
                                                         'ingredient'),
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления')
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

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
                               related_name='recipes',
                               verbose_name='Рецепт')
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        """Meta class for Recipe model."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class UserRecipeModelMixin(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               null=True,
                               default=None)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_recipe_list'
            )
        ]
        abstract = True


class ShoppingCart(UserRecipeModelMixin):

    class Meta:

        default_related_name = 'shopping'
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self):
        return f'Список покупок пользователя {self.user.username}'


class Favourites(UserRecipeModelMixin):

    class Meta:

        default_related_name = 'favourites'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        return f'Избранный рецепт "{self.recipe}" у {self.user.username}'
