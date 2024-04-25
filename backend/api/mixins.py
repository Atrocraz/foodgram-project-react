from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe
from users.models import Follow

User = get_user_model()


class SubSerializerMixin():
    'Миксин для сериализаторов, содержащих поле is_subscribed.'

    def get_is_subscribed(self, obj):
        'Возвращает True, если автор запроса подписан на пользователя obj'

        request = self.context['request']
        if request is None or not request.user.is_authenticated:
            return False

        return Follow.objects.filter(
            following=obj,
            user=request.user).exists()


class PostDeleteDBMixin():
    '''Миксин для обработки POST и DELETE запросов для моделей Follow,
    Favourites и ShoppingCart.
    '''

    @staticmethod
    def process_request(request, model=None, serializer_cls=None,
                        err_msg="", attrs=None):
        '''Метод класса, отвечающий за обработку POST и DELETE запросов.

        В качестве аргументов принимает: объект request, модель,
        класс сериализатора, шаблон сообщения об ошибке и атрибуты для
        сериализатора.
        '''

        user = request.user
        data = {'user': user.id, }
        data.update(attrs)

        if request.method == "POST":
            if 'recipe' in attrs:
                if not Recipe.objects.filter(pk=attrs['recipe']).exists():
                    return Response(
                        {"errors": (f'Рецепт с id {attrs["recipe"]} '
                                    'не существует')},
                        status=status.HTTP_400_BAD_REQUEST)

            serializer = serializer_cls(
                data=data,
                context={'request': request, })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            if 'recipe' in attrs:
                get_object_or_404(Recipe, pk=attrs['recipe'])

            instance = model.objects.filter(**data)
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {"errors": err_msg},
                status=status.HTTP_400_BAD_REQUEST)
