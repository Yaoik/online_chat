from rest_framework import serializers
from .models import Channel, ChannelMembership, Message, Invitation
from users.serializers import UserSerializer
from typing import cast
from users.models import User
from datetime import timedelta
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .choices import ExpirationTime

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
        fields = ['uuid', 'channel', 'user', 'content', 'timestamp', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'timestamp', 'created_at', 'updated_at', 'user']


class ChannelCreateSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Channel
        fields = ['uuid', 'name', 'owner', 'created_at']
        read_only_fields = ['uuid', 'created_at']

class ChannelMembershipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelMembership
        fields = ['user', 'channel', 'is_admin']
        extra_kwargs = {
            'is_admin': {'required': False}
        }


class MessageCreateSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['channel', 'content']
        extra_kwargs = {
            'content': {'required': True}
        }

class InvitationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = ['token', 'author', 'channel', 'expires_in', 'expiration_period', 'is_expired']
        read_only_fields = fields
    
    def get_is_expired(self, obj:Invitation) -> bool:
        return obj.is_expired
    
class InvitationCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    
    class Meta:
        model = Invitation
        fields = ['token', 'author', 'channel', 'expires_in', 'expiration_period']
        read_only_fields = ['token', 'expires_in']
    
    def validate_expiration_period(self, expiration_period:str):
        if expiration_period not in ExpirationTime.values:
            raise serializers.ValidationError("Недопустимый срок действия.")
        return super().validate(expiration_period)