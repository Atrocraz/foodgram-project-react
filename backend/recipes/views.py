from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .models import Ingredient, Recipe, Tag
from .permissions import AdvancedPermission
from .serializers import (IngredientSerializer, ReadRecipeSerializer,
                          TagSerializer, WriteRecipeSerializer)


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
