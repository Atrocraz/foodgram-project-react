from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe

User = get_user_model()


class IngredientFilter(FilterSet):
    '''Фильтр для эндпоинта api/ingredients.

    Позволяет производить фильтрацию по частичному
    совпадению начальных символов названия.
    '''

    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        'Класс Meta для фильтра'

        model = Ingredient
        fields = ('name',)


class RecipesFilter(FilterSet):
    '''Фильтр для эндпоинта api/recipes/.. .

    Позволяет производить фильтрацию по автору,
    нескольким тэгам и наличию рецепта в избранном
    или списке покупок.
    '''

    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        'Класс Meta для фильтра'

        model = Recipe
        fields = ["author", "tags"]

    def filter_is_favorited(self, queryset, name, value):
        '''Метод класса фильтра.

        Предопределяет работу фильтрации по полю is_favorited'''

        if value:
            return queryset.filter(favourites__user=self.request.user.id)

        return queryset.objects.all()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        '''Метод класса фильтра.

        Предопределяет работу фильтрации по полю is_favorited'''

        if value:
            return queryset.filter(
                shopping__user=self.request.user.id)

        return queryset.objects.all()
