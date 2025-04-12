from django.urls import re_path
from django.urls import path
from .views import (
    ChannelView,
    InvitationView,
    ChannelConnectView,
    MessageView
)
from rest_framework.routers import DefaultRouter
from .views import ChannelView, MessageView
from .consumers import MainConsumer


urlpatterns = [
    path(
        'api/channels/',
        ChannelView.as_view({'get': 'list', 'post': 'create'}),
        name='channels-list'
    ),
    path(
        'api/channels/<uuid:channel_uuid>/',
        ChannelView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}),
        name='channels-detail'
    ),
    
    path(
        'api/channels/<uuid:channel_uuid>/messages/',
        MessageView.as_view({'get': 'list', 'post': 'create'}),
        name='channel-messages-list'
    ),
    path(
        'api/channels/<uuid:channel_uuid>/messages/<uuid:message_uuid>/',
        MessageView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}),
        name='channel-messages-detail'
    ),
    
    path(
        'api/channels/<uuid:channel_uuid>/invitations/', 
        InvitationView.as_view({'get': 'list', 'post': 'create'}), 
        name='channel-invitations-list'
    ),
    path(
        'api/channels/<uuid:channel_uuid>/invitations/<uuid:invitation_uuid>/', 
        InvitationView.as_view({'get': 'retrieve', 'delete': 'destroy'}), 
        name='channel-invitations-detail',
    ),
    path(
        'api/channels/connect/<uuid:invitation_uuid>/', 
        ChannelConnectView.as_view(), 
        name='channel-invitations-accept'
    ),
]

websocket_urlpatterns = [
    re_path(r'ws/main/$', MainConsumer.as_asgi()),
]