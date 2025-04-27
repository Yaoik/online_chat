
from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['uuid', 'user', 'content', 'created_at', 'updated_at', 'is_deleted', 'number']
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'user', 'is_deleted', 'number']

    def to_representation(self, instance: Message):
        representation = super().to_representation(instance)
        if instance.is_deleted:
            representation['content'] = "Сообщение удалено."
        return representation


class MessageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ('channel', 'content')
        extra_kwargs = {
            'content': {'required': True}
        }
        read_only_fields = ('channel',)

    def to_representation(self, instance: Message):
        return MessageSerializer(instance).to_representation(instance)

    def validate_content(self, value: str):
        if self.instance and self.instance.is_deleted:
            raise serializers.ValidationError("Нельзя обновлять содержимое удалённого сообщения")
        return value
