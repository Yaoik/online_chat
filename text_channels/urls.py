from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    ChannelBanListView,
    ChannelConnectView,
    ChannelCreateDeleteBanView,
    ChannelDisconnectView,
    ChannelView,
)

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
        'api/channels/connect/<uuid:invitation_uuid>/',
        ChannelConnectView.as_view(),
        name='channel-invitations-connect'
    ),
    path(
        'api/channels/disconnect/<uuid:channel_uuid>/',
        ChannelDisconnectView.as_view(),
        name='channel-invitations-disconnect'
    ),
    path(
        'api/channels/<uuid:channel_uuid>/bans/',
        ChannelBanListView.as_view(),
        name='channel-ban-list'
    ),
    path(
        'api/channels/<uuid:channel_uuid>/bans/<int:user_id>/',
        ChannelCreateDeleteBanView.as_view(),
        name='channel-ban-detail'
    ),
]
