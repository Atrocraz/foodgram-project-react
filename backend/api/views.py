from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .permissions import AdvancedPermission
from .serializers import (CustomAuthSerializer, IngredientSerializer,
                          ReadFollowSerializer, ReadRecipeSerializer,
                          TagSerializer, WriteFollowSerializer,
                          WriteRecipeSerializer)
from recipes.models import Ingredient, Recipe, Tag
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


class CustomUserViewSet(UserViewSet):

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
        user = request.user
        get_object_or_404(User.objects.all(), id=id)

        subscription = Follow.objects.filter(following_id=id,
                                             user_id=user.id)
        if request.method == "POST":
            serializer = WriteFollowSerializer(
                data={
                    'user': user.id,
                    'following': id
                    },
                context={'request': request, })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {"errors": "Подписка на пользователя не оформлена"},
                status=status.HTTP_400_BAD_REQUEST)

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
        mixins.CreateModelMixin,  # не забыть убрать
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def filter_ingredients(self):
        return Ingredient.objects.filter(
            Q(name__startswith=self.request.GET.get('name'))).values()

    def get_queryset(self):
        if self.request.GET.get('name') is not None:
            return self.filter_ingredients().all()

        return Ingredient.objects.all()


class RecipeViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin, mixins.ListModelMixin,
                    mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [AdvancedPermission]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadRecipeSerializer
        if self.action in ['create', 'delete', 'update', 'partial_update']:
            return WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, )
