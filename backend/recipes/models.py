from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from recipes.utils import get_rnd_hex_color

User = get_user_model()


class Tag(models.Model):
    """Класс модели тэга.

    Содержит поля названия, цвета и слага тэга.
    """

    name = models.CharField(max_length=settings.TAG_NAME_MAX_LEN,
                            verbose_name='Название',
                            unique=True)
    color = ColorField(unique=True,
                       max_length=settings.TAG_COLOR_MAX_LEN,
                       verbose_name='Цветовой код',
                       default=get_rnd_hex_color)
    slug = models.SlugField(max_length=settings.TAG_SLUG_MAX_LEN,
                            unique=True,
                            verbose_name='Слаг')

    class Meta:
        """Класс Meta модели."""

        ordering = ('name',)
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        """Строковое представление модели."""
        return f'{self.name}'


class Ingredient(models.Model):
    """Класс модели ингредиента.

    Содержит поля названия и ед. измерения ингредиента.
    """

    name = models.CharField(max_length=settings.INGREDIENT_NAME_MAX_LEN,
                            verbose_name='Название')

    measurement_unit = models.CharField(
        max_length=settings.MEAS_UNIT_NAME_MAX_LEN,
        verbose_name='Единица измерения')

    class Meta:
        """Класс Meta модели."""

        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_unit_list'
            )
        ]

    def __str__(self):
        'Строковое представление модели.'
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Класс модели рецепта.

    Содержит поля автора, названия, изображения, текстовог описания,
    ингредиентов, тэгов, времени приготовления и даты публикации.
    """

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField(max_length=settings.RECIPE_NAME_MAX_LEN,
                            verbose_name='Название')
    image = models.ImageField(
        'Ссылка на изображение',
        upload_to='recipes/images/'
    )
    text = models.TextField(verbose_name='Текстовое описание')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         through_fields=('recipe',
                                                         'ingredient'),
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(settings.RECIPE_MIN_COOKING_TIME)])
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        """Класс Meta модели."""

        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Строковое представление модели."""
        return f'{self.name}'


class RecipeIngredient(models.Model):
    """Класс промежуточной модели для моделей рецепта и ингредиента.

    Содержит дополнительное поле количества ингредиента.
    """

    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='recipe_ingredients')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipe_ingredients',
                               verbose_name='Рецепт')
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        """Класс Meta модели."""

        ordering = ('recipe',)
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        """Строковое представление модели."""
        return f'{self.ingredient} {self.recipe}'


class UserRecipeModelMixin(models.Model):
    """Родительская абстрактная модель для списка покупок и
    избранного.

    Содержит поля пользоватя и рецепта ингредиента и валидацию
    уникальности их сочетания.
    """

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               null=True,
                               default=None)

    class Meta:
        """Класс Meta модели."""

        abstract = True
        ordering = ('user',)


class ShoppingCart(UserRecipeModelMixin):
    """Модель для списка покупок."""

    class Meta(UserRecipeModelMixin.Meta):
        """Класс Meta модели."""

        default_related_name = 'shopping_carts'
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_recipe'
            )
        ]

    def __str__(self):
        """Строковое представление модели."""
        return f'Список покупок пользователя {self.user.username}'


class Favourites(UserRecipeModelMixin):
    """Модель для избранного."""

    class Meta(UserRecipeModelMixin.Meta):
        """Класс Meta модели."""

        default_related_name = 'favourites'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        """Строковое представление модели."""
        return f'Избранный рецепт "{self.recipe}" у {self.user.username}'
