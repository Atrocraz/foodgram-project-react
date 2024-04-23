from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response

from users.models import Follow

User = get_user_model()


class SubSerializerMixin():

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if request is None or not request.user.is_authenticated:
            return False

        return Follow.objects.filter(
            following=obj,
            user=request.user).exists()


class PostDeleteDBMixin():

    @staticmethod
    def process_request(request, model=None, serializer_cls=None,
                        err_msg="", attrs=None):
        user = request.user
        data = {'user': user.id, }
        data.update(attrs)

        if request.method == "POST":
            serializer = serializer_cls(
                data=data,
                context={'request': request, })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            subscription = model.objects.filter(**data)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {"errors": err_msg},
                status=status.HTTP_400_BAD_REQUEST)
