

from rest_framework import serializers

from text_channels.serializers import MiniChannelSerializer
from users.serializers import UserSerializer

from .choices import ExpirationTimeChoices
from .models import Invitation


class InvitationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = MiniChannelSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    accepted_users_count = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = ['uuid', 'author', 'channel', 'expires_in', 'expiration_period',
                  'created_at', 'is_expired', 'accepted_users_count']
        read_only_fields = fields

    def get_is_expired(self, obj: Invitation) -> bool:
        return obj.is_expired

    def get_accepted_users_count(self, obj: Invitation) -> int:
        return obj.acceptances.count()  # type: ignore


class InvitationCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    channel = MiniChannelSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ['uuid', 'author', 'channel', 'expires_in', 'created_at', 'expiration_period']
        read_only_fields = ['uuid', 'expires_in']

    def validate_expiration_period(self, expiration_period: str):
        if expiration_period not in ExpirationTimeChoices.values:
            raise serializers.ValidationError("Недопустимый срок действия.")
        return super().validate(expiration_period)
