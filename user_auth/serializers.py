from rest_framework import serializers


class TokenResponseSerializer(serializers.Serializer):
    """
    Только для указания Response в drf_spectacular.
    """
    token = serializers.CharField(help_text="JWT token for WebSocket authentication")
