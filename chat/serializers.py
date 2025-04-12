from rest_framework import serializers
from .models import Channel, ChannelMembership, Message, Invitation
from users.serializers import UserSerializer
from typing import cast
from users.models import User
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError


class ChannelSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at']
        read_only_fields = ['uuid', 'name', 'created_at']

class ChannelMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    
    class Meta:
        model = ChannelMembership
        fields = ['id', 'user', 'channel', 'is_admin', 'is_baned']
        read_only_fields = ['id', 'user', 'channel']


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'channel', 'user', 'content', 'timestamp', 'created_at', 'updated_at']
        read_only_fields = ['id', 'timestamp', 'created_at', 'updated_at', 'user']


class ChannelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at']
        read_only_fields = ['uuid', 'owner', 'created_at']

class ChannelMembershipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelMembership
        fields = ['user', 'channel', 'is_admin']
        extra_kwargs = {
            'is_admin': {'required': False}
        }


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['channel', 'content']
        extra_kwargs = {
            'content': {'required': True}
        }

class InvitationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    
    class Meta:
        model = Invitation
        fields = ['token', 'author', 'channel', 'expires_in']
        read_only_fields = fields
    
class InvitationCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    
    class Meta:
        model = Invitation
        fields = ['token', 'author', 'channel', 'expires_in']
        read_only_fields = ['token', 'author', 'channel']
    
    def validate_expires_in(self, expires_in):
        if expires_in > datetime.now() + timedelta(days=1):
            raise ValidationError(detail='expires_in не может быть больше чем +1 день от текущего времени')
        if expires_in < datetime.now():
            raise ValidationError(detail='expires_in не может быть меньше текущей даты')
        return super().validate(expires_in)