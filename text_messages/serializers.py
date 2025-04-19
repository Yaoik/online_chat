
from rest_framework import serializers

from text_channels.serializers import ChannelSerializer
from users.serializers import UserSerializer

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['uuid', 'channel', 'user', 'content', 'timestamp', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'timestamp', 'created_at', 'updated_at', 'user']


class MessageCreateSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['channel', 'content']
        extra_kwargs = {
            'content': {'required': True}
        }
