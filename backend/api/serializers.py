from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favourites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class FoodgramUserCreateSerializer(UserCreateSerializer):
    """Класс-сериализатор для создания модели MyUser."""

    class Meta:
        """Класс Meta сериализатора."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')


class FoodgramUserSerializer(UserSerializer):
    """Класс-сериализатор для чтения модели MyUser."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Класс Meta сериализатора."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """Возвращает True, если автор запроса подписан на пользователя obj."""
        request = self.context['request']
        return (request is not None and request.user.is_authenticated
                and obj.following.filter(user=request.user).exists())


class ReadFollowSerializer(FoodgramUserSerializer):
    """Класс-сериализатор для возврата ответа на запрос к модели Follow."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        """Класс Meta сериализатора."""

        model = User
        fields = FoodgramUserSerializer.Meta.fields + ('recipes',
                                                       'recipes_count')

    def get_recipes(self, obj):
        """Метод для получения значения поля repices."""
        queryset = Recipe.objects.filter(author=obj)
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
        serializer = UsersRecipeSerializer(queryset, many=True)

        return serializer.data


class WriteFollowSerializer(serializers.ModelSerializer):
    """Класс-сериализатор для записи в модель Follow."""

    class Meta:
        """Класс Meta сериализатора."""

        model = Follow
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Подписка на этого пользователя уже оформлена')
        ]

    def validate(self, data):
        """Валидатор поля following сериализатора.

        Вызывает ValidationError, если пользователь пытается подписаться
        на самого себя.
        """
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        return data

    def to_representation(self, instance):
        """Метод для переопределения полей ответа на запрос."""
        return ReadFollowSerializer(instance=instance.following,
                                    context=self.context).data


class FoodgramAuthSerializer(serializers.Serializer):
    """Cериализатор для авторизации пользователя и получения токена."""

    email = serializers.CharField(
        label=_("Email"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """Класс-сериализатор для модели Tag."""

    class Meta:
        """Класс Meta сериализатора."""

        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Класс-сериализатор для модели Ingredient."""

    class Meta:
        """Класс Meta сериализатора."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class WriteIngredientRecipeSerializer(serializers.ModelSerializer):
    """Класс-сериализатор для записи в модель RecipeIngredient."""

    id = serializers.PrimaryKeyRelatedField(source='ingredient',
                                            queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=settings.RECIPE_INGREDIENT_MIN_AMOUNT)

    class Meta:
        """Класс Meta сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class GetIngredientRecipeSerializer(serializers.ModelSerializer):
    """Класс-сериализатор модели RecipeIngredient.

    Обрабатывает данные для возврата ответа на запрос к модели.
    """

    id = serializers.PrimaryKeyRelatedField(source='ingredient',
                                            queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        required=True,
        min_value=settings.RECIPE_MIN_COOKING_TIME)

    class Meta:
        """Класс Meta сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class WriteRecipeSerializer(serializers.ModelSerializer):
    """Класс-сериализатор для записи в модель Recipe."""

    author = FoodgramUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    image = Base64ImageField()
    ingredients = WriteIngredientRecipeSerializer(many=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        """Класс Meta сериализатора."""

        model = Recipe
        fields = ('author', 'name', 'image', 'text', 'cooking_time',
                  'ingredients', 'tags')

    @transaction.atomic
    def db_workout(self, instance, validated_data):
        """Метод для создания и обновления модели Recipe."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        if instance is None:
            validated_data['author'] = self.context['request'].user
            instance = Recipe.objects.create(**validated_data)
        else:
            RecipeIngredient.objects.filter(recipe=instance).all().delete()
            super().update(instance=instance, validated_data=validated_data)

        instance.tags.clear()
        instance.tags.set(tags)

        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        )

        return instance

    def create(self, validated_data):
        """Хук-метод для создания модели Recipe."""
        recipe = self.db_workout(None, validated_data)

        return recipe

    def update(self, instance, validated_data):
        """Хук-метод для обновления модели Recipe."""
        instance = self.db_workout(instance, validated_data)

        return instance

    def to_representation(self, instance):
        """Метод для переопределения полей ответа на запрос."""
        return ReadRecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        """Метод для валидации содержимого полей перед созданием рецепта."""
        image = data.get('image')
        if not image:
            raise serializers.ValidationError(
                'Отсутствует фото'
            )

        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Минимальное число ингредиентов: 1'
            )

        ingredients_ids = [
            ingredient['ingredient'].id for ingredient in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                'Этот ингредиент уже добавлен.'
            )

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Минимальное число тегов: 1'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Этот тег уже добавлен.')

        return data


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Класс-сериализатор для возврата ответа на запрос к модели Recipe."""

    author = FoodgramUserSerializer(read_only=True)
    ingredients = GetIngredientRecipeSerializer(source='recipe_ingredients',
                                                many=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False)

    class Meta:
        """Класс Meta сериализатора."""

        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        depth = 1


class BaseFavouriteCartSerializer(serializers.ModelSerializer):
    """Родительский класс сериализатора.

    Нужен в качестве миксина для сериализаторов моделейFavourites и
    ShoppingCart.
    """

    class Meta:
        """Класс Meta сериализатора."""

        model = None
        fields = ('user', 'recipe')

    def validate(self, data):
        """Метод для валидации содержимого поля recipe."""
        if not Recipe.objects.filter(pk=data['recipe'].id).exists():
            raise serializers.ValidationError(
                {"errors": (f'Рецепт с id {data["recipe"]} '
                 'не существует')}
            )
        return data

    def to_representation(self, instance):
        """Метод для переопределения полей ответа на запрос."""
        return UsersRecipeSerializer(instance=instance.recipe,
                                     context=self.context).data


class FavouritesSerializer(BaseFavouriteCartSerializer):
    """Класс-сериализатор для модели Favourites."""

    class Meta:
        """Класс Meta сериализатора."""

        model = Favourites
        fields = BaseFavouriteCartSerializer.Meta.fields
        validators = [
            UniqueTogetherValidator(
                queryset=Favourites.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном')
        ]


class ShoppingCartSerializer(BaseFavouriteCartSerializer):
    """Класс-сериализатор для модели ShoppingCart."""

    class Meta:
        """Класс Meta сериализатора."""

        model = ShoppingCart
        fields = BaseFavouriteCartSerializer.Meta.fields
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок')
        ]


class UsersRecipeSerializer(serializers.ModelSerializer):
    """Cериализатор чтения рецептов для подписок, избранного и корзины."""

    image = Base64ImageField()

    class Meta:
        """Класс Meta сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
