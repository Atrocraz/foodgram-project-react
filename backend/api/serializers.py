from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .mixins import UserSerializerMixin
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Follow

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    "Класс-сериализатор для модели MyUser"

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')


class CustomUserSerializer(UserSerializer, UserSerializerMixin):
    "Класс-сериализатор для модели MyUser"

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class ReadFollowSerializer(UserSerializerMixin):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        queryset = Recipe.objects.filter(author=obj)
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]

        serializer = UsersRecipeSerializer(queryset, many=True)

        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class WriteFollowSerializer(serializers.ModelSerializer):
    """Follow model serializer."""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all())
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all())

    class Meta:
        """Meta class for FollowSerializer."""

        model = Follow
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Подписка на этого пользователя уже оформлена')
        ]

    def validate(self, data):
        """Following field validator for FollowSerializer."""
        if self.context['request'].user == data['following']:
            # Проверить, должна ли быть в тексте ошибки строка
            # или список тоже работает
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        return data

    def to_representation(self, instance):
        return ReadFollowSerializer(
            instance=User.objects.get(pk=instance.following_id),
            context=self.context).data


class CustomAuthSerializer(serializers.Serializer):
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

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class WriteIngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class GetIngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient',
                                            queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class WriteRecipeSerializer(serializers.ModelSerializer):

    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = WriteIngredientRecipeSerializer(many=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = Recipe
        fields = ('author', 'name', 'image', 'text', 'cooking_time',
                  'ingredients', 'tags')

    @transaction.atomic
    def db_workout(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        if instance is None:
            instance = Recipe.objects.create(**validated_data)
        else:
            instance.name = validated_data.get('name', instance.name)
            instance.text = validated_data.get('text', instance.text)
            instance.image = validated_data.get('image', instance.image)
            instance.cooking_time = validated_data.get('cooking_time',
                                                       instance.cooking_time)
            RecipeIngredient.objects.filter(recipe=instance).all().delete()
            instance.save()

        instance.tags.clear()
        instance.tags.set(tags)

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=instance,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount'],
            ) for ingredient in ingredients
        ])

        return instance

    def create(self, validated_data):
        recipe = self.db_workout(None, validated_data)

        return recipe

    def update(self, instance, validated_data):
        instance = self.db_workout(instance, validated_data)

        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class ReadRecipeSerializer(serializers.ModelSerializer):

    author = CustomUserSerializer(read_only=True)
    ingredients = GetIngredientRecipeSerializer(source='recipes', many=True)
    is_favourited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favourited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        depth = 1

    def get_is_favourited(self, obj):
        pass

    def get_is_in_shopping_cart(self, obj):
        pass


class UsersRecipeSerializer(serializers.ModelSerializer):
    """Cериализатор чтения рецептов
    для подписок, избранного и корзины. """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
