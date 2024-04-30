from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipesFilter
from api.mixins import PostDeleteDBMixin
from api.pagination import PageAndLimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CustomAuthSerializer, FavouritesSerializer,
                             IngredientSerializer, ReadFollowSerializer,
                             ReadRecipeSerializer, ShoppingCartSerializer,
                             TagSerializer, WriteFollowSerializer,
                             WriteRecipeSerializer)
from recipes.models import (Favourites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow


User = get_user_model()


class CustomAuthToken(ObtainAuthToken):
    """Вьюсет для переопределения ответа на запрос токена."""

    serializer_class = CustomAuthSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class CustomUserViewSet(UserViewSet, PostDeleteDBMixin):
    """Вьюсет для переопределения методов UserViewSet библиотеки Djoser.

    Обрабатывает все эндпоинты модели пользователя, которые предоставляет
    Djoser и эндпоинты модели Follow.
    """

    @action(["get", "put", "patch", "delete"],
            detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy(request, *args, **kwargs)

    @action(["post", "delete"],
            detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Метод для обработки запросов создания и удаления подписки."""
        get_object_or_404(User.objects.all(), id=id)
        data = {'following': id, }
        return self.process_request(request, Follow, WriteFollowSerializer,
                                    "Подписка на пользователя не оформлена",
                                    data)

    @action(["get", ],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request, *args, **kwargs):
        """Метод для обработки запроса списка действующих подписок."""
        user = request.user
        queryset = (
            User.objects
            .filter(following__user=user)
        )
        pages = self.paginate_queryset(queryset)
        serializer = ReadFollowSerializer(
            pages,
            many=True,
            context={'request': request, })
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки GET запросов к модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки GET запросов к модели Ingredient."""

    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet, PostDeleteDBMixin):
    """Вьюсет для обработки GET, POST, UPDATE и DELETE запросов
    к модели Ingredient.
    """

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = PageAndLimitPagination

    def get_queryset(self):
        """Переопределение логики метода для аннотации полей.

        Для авторизованных пользователей в сериализатор будут переданы
        значения полей is_favorited и is_in_shopping_cart.
        """
        queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'ingredients'
        )
        if not self.request.user.is_authenticated:
            return queryset.all()

        return (
            queryset.annotate(
                is_favorited=Exists(
                    Favourites.objects.filter(
                        recipe=OuterRef('id'),
                        user=self.request.user
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        recipe=OuterRef('id'),
                        user=self.request.user
                    )
                )
            ).all()
        )

    def get_serializer_class(self):
        """Переопределение метода для выбора сериализатора в зависимости от
        типа запроса.
        """
        if self.action in ['list', 'retrieve']:
            return ReadRecipeSerializer

        return WriteRecipeSerializer

    @action(["post", "delete"],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Метод для обработки запросов создания и удаления избранного."""
        data = {'recipe': pk, }
        return self.process_request(request, Favourites,
                                    FavouritesSerializer,
                                    "Рецепт не находится в избранном", data)

    @action(["post", "delete"],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Метод для обработки запросов добавления и удаления
        из списка покупок.
        """
        data = {'recipe': pk, }
        return self.process_request(request, ShoppingCart,
                                    ShoppingCartSerializer,
                                    "Рецепт не находится в списке покупок",
                                    data)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Метод для обработки запроса получения списка покупок
        в виде файла.
        """
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values_list(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(total=Sum('amount'))

        return self.return_file_in_responser(ingredients=ingredients)

    @staticmethod
    def return_file_in_responser(ingredients):
        """Метод для формирования текстового списка ингредиентов."""
        shopping_result = []
        for ingredient in ingredients:
            shopping_result.append(
                f'{ingredient[0]} - '
                f'{ingredient[2]} '
                f'({ingredient[1]})'
            )
        shopping_itog = '\n'.join(shopping_result)
        response = FileResponse(
            shopping_itog,
            content_type='text/plain',
            as_attachment=True,
            filename='Список покупок.txt'
        )
        return response
