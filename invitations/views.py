import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from text_channels.models import Channel

from .models import Invitation
from .permissions import InvitationPermissions
from .serializers import InvitationCreateSerializer, InvitationSerializer

logger = logging.getLogger(__name__)


class InvitationChannelPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses=InvitationSerializer,
    )
    def get(self, request: Request, *args, **kwargs):
        invitation_uuid = kwargs.get('invitation_uuid', None)
        invitation = get_object_or_404(Invitation, uuid=invitation_uuid)
        serializer = InvitationSerializer(invitation)
        return Response(serializer.data)


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
        if self.action in ('retrieve', 'destroy'):
            return Invitation.objects.filter(expires_in__gt=timezone.now()).order_by('-expires_in')
        channel_uuid = self.kwargs['channel_uuid']
        return Invitation.objects.filter(Q(channel__uuid=channel_uuid) & Q(expires_in__gt=timezone.now())).order_by('-expires_in')

    def perform_create(self, serializer: InvitationCreateSerializer):
        user = self.request.user
        channel_uuid = self.kwargs['channel_uuid']
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        serializer.save(channel=channel, author=user)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
        return super().destroy(request, *args, **kwargs)
