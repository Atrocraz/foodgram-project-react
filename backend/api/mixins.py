from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe

User = get_user_model()


class PostDeleteDBMixin:
    """Миксин для обработки запросов.

    Обрабатывает запросы POST и DELETE для моделей Follow,
    Favourites и ShoppingCart.
    """

    @staticmethod
    def process_request(request, model=None, serializer_cls=None,
                        err_msg="", attrs=None):
        """Метод класса, отвечающий за обработку POST и DELETE запросов.

        В качестве аргументов принимает: объект request, модель,
        класс сериализатора, шаблон сообщения об ошибке и атрибуты для
        сериализатора.
        """
        user = request.user
        data = {'user': user.id, }
        data.update(attrs)

        if request.method == "POST":
            serializer = serializer_cls(
                data=data,
                context={'request': request,
                         'err_msg': err_msg})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if 'recipe' in attrs:
            get_object_or_404(Recipe, pk=data['recipe'])

        instance = model.objects.filter(**data)
        if not instance.exists():
            return Response(
                {"errors": err_msg},
                status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
