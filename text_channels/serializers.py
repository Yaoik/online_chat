
from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from text_messages.models import Message
from text_messages.serializers import MessageSerializer
from users.serializers import UserSerializer

from .models import Channel, ChannelMembership


class ChannelSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at', 'last_message']
        read_only_fields = ['uuid', 'name', 'created_at', 'last_message']

    @extend_schema_field(MessageSerializer(allow_null=True))
    def get_last_message(self, obj: Channel):
        last_message = Message.objects.filter(channel=obj).order_by('-timestamp').first()
        if last_message:
            data = MessageSerializer(last_message).data
            content_length = len(data['content'])
            if content_length > settings.CHANNEL_LAST_MESSAGE_MAX_LENGTH:
                data['content'] = data['content'][:settings.CHANNEL_LAST_MESSAGE_MAX_LENGTH] + '...'
            return data


class ChannelCreateSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at']
        read_only_fields = ['uuid', 'created_at']


class ChannelMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = ChannelMembership
        fields = ['id', 'user', 'channel', 'is_admin', 'is_baned']
        read_only_fields = fields


class ChannelMembershipCreateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = ChannelMembership
        fields = ['id', 'user', 'channel', 'is_admin', 'is_baned']
        read_only_fields = ['id', 'user', 'channel', 'is_admin', 'is_baned']
