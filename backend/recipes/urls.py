from django.urls import include, path
from rest_framework import routers

import recipes.views as views

router_v1 = routers.DefaultRouter()
router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register('ingredients',
                   views.IngredientViewSet,
                   basename='ingredients')
router_v1.register('recipes', views.RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
]
