from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import Follow

User = get_user_model()


class UserSerializerMixin(serializers.ModelSerializer):
    "Класс-сериализатор для модели MyUser"
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if not request.user.is_authenticated:
            return 'False'

        if Follow.objects.filter(
                following=obj,
                user_id=request.user.id).count() > 0:

            return 'True'

        return 'False'
