from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Ingredient, Recipe, RecipeIngredient, Tag
from users.serializers import CustomUserSerializer

User = get_user_model()


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
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
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
