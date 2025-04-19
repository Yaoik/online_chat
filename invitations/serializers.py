

from rest_framework import serializers

from text_channels.serializers import ChannelSerializer
from users.serializers import UserSerializer

from .choices import ExpirationTime
from .models import Invitation


class InvitationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = ['uuid', 'author', 'channel', 'expires_in', 'expiration_period', 'is_expired']
        read_only_fields = fields

    def get_is_expired(self, obj: Invitation) -> bool:
        return obj.is_expired


class InvitationCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ['uuid', 'author', 'channel', 'expires_in', 'expiration_period']
        read_only_fields = ['uuid', 'expires_in']

    def validate_expiration_period(self, expiration_period: str):
        if expiration_period not in ExpirationTime.values:
            raise serializers.ValidationError("Недопустимый срок действия.")
        return super().validate(expiration_period)
