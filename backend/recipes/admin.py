from django.contrib import admin

from .models import (Favourites, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    '''Модель для администрирования ингредиентов.'''

    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    '''Инлайн для отображения ингредиентов в рецептах.'''

    model = RecipeIngredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    '''Модель для администрирования тегов.'''

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color')
    list_filter = ('name', 'color')


class TagInline(admin.TabularInline):
    '''Инлайн для отображения тегов в рецептах. '''

    model = Recipe.tags.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    '''Модель для администрирования рецептов.'''

    inlines = (RecipeIngredientInline, TagInline)
    list_display = (
        'name',
        'text',
        'author',
        'pub_date',
        'cooking_time',
        'display_ingredients',
        'favorite_count',
        'display_tags'
    )
    search_fields = ('name', 'author__username', 'favorite_count')
    list_filter = ('name', 'author', 'tags')

    @admin.display(description='Добавили в избранное')
    def favorite_count(self, obj):
        return obj.favorite.count()

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, recipe):
        return recipe.ingredients.values_list(
            'name', flat=True
        ).order_by('name')

    @admin.display(description='Теги')
    def display_tags(self, recipe):
        return recipe.tags.values_list(
            'name', flat=True
        ).order_by('name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    '''Модель для администрирования  списков покупок.'''

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)


@admin.register(Favourites)
class FavoriteAdmin(ShoppingCartAdmin):
    '''Модель для администрирования избранного.'''
