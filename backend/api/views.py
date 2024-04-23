from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipesFilter
from .mixins import PostDeleteDBMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomAuthSerializer, FavouritesSerializer,
                          IngredientSerializer, ReadFollowSerializer,
                          ReadRecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, WriteFollowSerializer,
                          WriteRecipeSerializer)
from recipes.models import Favourites, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow

User = get_user_model()


class CustomAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class CustomUserViewSet(UserViewSet, PostDeleteDBMixin):

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
        get_object_or_404(User.objects.all(), id=id)
        data = {'following': id, }
        return self.process_request(request, Follow, WriteFollowSerializer,
                                    "Подписка на пользователя не оформлена",
                                    data)

    @action(["get", ],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request, *args, **kwargs):
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


class TagViewSet(
        mixins.CreateModelMixin,  # не забыть убрать
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class RecipeViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin, mixins.ListModelMixin,
                    mixins.DestroyModelMixin, viewsets.GenericViewSet,
                    PostDeleteDBMixin):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
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
        if self.action in ['list', 'retrieve']:
            return ReadRecipeSerializer
        if self.action in ['create', 'delete', 'update', 'partial_update']:
            return WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, )

    @action(["post", "delete"],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)

        data = {'recipe': pk, }
        return self.process_request(request, Favourites,
                                    FavouritesSerializer,
                                    "Рецепт не находится в избранном", data)

    @action(["post", "delete"],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)

        data = {'recipe': pk, }
        return self.process_request(request, ShoppingCart,
                                    ShoppingCartSerializer,
                                    "Рецепт не находится в списке покупок",
                                    data)
