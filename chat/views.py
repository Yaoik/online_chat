from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import status
#from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
#from typing import Any, cast
from .models import Channel, ChannelMembership, Invitation, Message
from .serializers import (
    ChannelCreateSerializer,
    ChannelSerializer,
    #ChannelMembershipCreateSerializer,
    #ChannelMembershipSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MessageCreateSerializer,
    MessageSerializer
)
#from rest_framework.generics import GenericAPIView
#from rest_framework import mixins
from .permissions import (
    IsChannelMember, 
    IsChannelAdmin, 
    IsMessageAuthorOrChannelAdmin,
    CanCreateInvitation,
)
import uuid
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

class ChannelView(
    ModelViewSet,
):  
    """
    Вьюшка для CRUD операций с каналами
    """
    permission_classes = [IsAuthenticated, IsChannelAdmin]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'channel_uuid'
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChannelCreateSerializer
        return ChannelSerializer

    def get_queryset(self):
        return Channel.objects.filter(memberships__user=self.request.user)

    def perform_create(self, serializer:ChannelCreateSerializer):
        user = self.request.user
        channel = serializer.save(owner=user)
        ChannelMembership.objects.create(
            user=user,
            channel=channel,
            is_admin=True,
        )
    

class InvitationCreateView(APIView):
    """
    Вьюшка для создания приглашения
    """
    permission_classes = [IsAuthenticated, IsChannelAdmin, CanCreateInvitation]
    serializer_class = InvitationSerializer

    def post(self, request:Request, channel_uuid:uuid.UUID):
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        self.check_object_permissions(request, channel)
        serializer = InvitationCreateSerializer(
            data={},
            context={'request': request, 'channel': channel}
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED
        )

class ChannelConnectView(APIView):
    """
    Вьюшка для подключения к каналу по приглашению.
    GET: возвращает данные канала, если токен валидный.
    POST: подключает пользователя к каналу и возвращает данные канала.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ChannelSerializer
    
    @extend_schema(
        request=None,
        responses=ChannelSerializer
    )
    def get(self, request:Request, channel_uuid:uuid.UUID, invitation_uuid:uuid.UUID):
        """
        Возвращает данные канала по валидному токену приглашения.
        """
        channel = get_object_or_404(Channel, uuid=channel_uuid)

        get_object_or_404(
            Invitation,
            token=invitation_uuid,
            channel=channel,
            is_expired=False
        )

        serializer = ChannelSerializer(channel)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=ChannelSerializer
    )
    def post(self, request:Request, channel_uuid:uuid.UUID, invitation_uuid:uuid.UUID):
        """
        Подключает пользователя к каналу по токену приглашения.
        """
        channel = get_object_or_404(Channel, uuid=channel_uuid)

        get_object_or_404(
            Invitation,
            token=invitation_uuid,
            channel=channel,
            is_expired=False
        )

        if ChannelMembership.objects.filter(
            user=request.user,
            channel=channel
        ).exists():
            return Response(
                {"error": "Вы уже участник этого канала"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ChannelMembership.objects.create(
            user=request.user,
            channel=channel,
            is_admin=False
        )

        serializer = ChannelSerializer(channel)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MessageView(
    ModelViewSet,
):
    """
    Вьюшка для всех CRUD операций с сообщениями
    """
    permission_classes = [IsAuthenticated, IsChannelMember, IsMessageAuthorOrChannelAdmin]
    serializer_class = MessageSerializer

    
    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        channel_uuid = self.kwargs['channel_uuid']
        return Message.objects.filter(channel_uuid=channel_uuid)

    def perform_create(self, serializer:MessageCreateSerializer):
        channel_uuid = self.kwargs['channel_uuid']
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        serializer.save(channel=channel)