
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from text_messages.models import Message
from text_messages.serializers import MessageSerializer
from users.models import User
from users.serializers import UserSerializer

from .models import Channel, ChannelMembership


class MiniChannelSerializer(serializers.ModelSerializer):
    """
    Используется в Invitations, не должен передавать чувствительные данные!
    """
    owner = UserSerializer(read_only=True)
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['name', 'owner', 'created_at', 'users_count']
        read_only_fields = ['name', 'owner', 'created_at', 'users_count']

    @extend_schema_field(OpenApiTypes.INT)
    def get_user_count(self, obj: Channel):
        return ChannelMembership.objects.filter(channel=obj).count()


class ChannelSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at', 'last_message', 'users']
        read_only_fields = ['uuid', 'name', 'owner', 'created_at', 'last_message', 'users']

    @extend_schema_field(MessageSerializer(allow_null=True))
    def get_last_message(self, obj: Channel):
        last_message = Message.objects.filter(channel=obj).order_by('-timestamp').first()
        if last_message:
            data = MessageSerializer(last_message).data
            content_length = len(data['content'])
            if content_length > settings.CHANNEL_LAST_MESSAGE_MAX_LENGTH:
                data['content'] = data['content'][:settings.CHANNEL_LAST_MESSAGE_MAX_LENGTH] + '...'
            return data

    @extend_schema_field(UserSerializer(many=True))
    def get_users(self, obj: Channel):
        memberships = ChannelMembership.objects.filter(channel=obj).select_related('user')
        users = [membership.user for membership in memberships]
        return UserSerializer(users, many=True).data


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
