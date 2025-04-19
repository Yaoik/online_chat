from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from text_channels.models import Channel

from .models import Invitation
from .permissions import InvitationPermissions
from .serializers import InvitationCreateSerializer, InvitationSerializer


class InvitationView(ModelViewSet):
    """
    Вьюшка для CRD приглашения
    """
    permission_classes = [IsAuthenticated, InvitationPermissions]
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'uuid'
    lookup_url_kwarg = 'invitation_uuid'

    def get_serializer_class(self):
        if self.action in ['create']:
            return InvitationCreateSerializer
        return InvitationSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return Invitation.objects.filter(expires_in__gt=timezone.now())
        channel_uuid = self.kwargs['channel_uuid']
        return Invitation.objects.filter(channel__uuid=channel_uuid)

    def perform_create(self, serializer: InvitationCreateSerializer):
        user = self.request.user
        channel_uuid = self.kwargs['channel_uuid']
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        serializer.save(channel=channel, author=user)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
