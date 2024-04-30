from django.urls import include, path
from djoser import views as dj_views
from rest_framework import routers

import api.views as views

router_v1 = routers.DefaultRouter()
router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register('ingredients',
                   views.IngredientViewSet,
                   basename='ingredients')
router_v1.register('recipes', views.RecipeViewSet, basename='recipes')
router_v1.register('users', views.CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/login/', views.CustomAuthToken.as_view()),
    path('auth/token/logout/', dj_views.TokenDestroyView.as_view()),
]
