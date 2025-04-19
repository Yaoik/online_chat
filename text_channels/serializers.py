
from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Channel, ChannelMembership


class ChannelSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at']
        read_only_fields = ['uuid', 'name', 'created_at']


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
