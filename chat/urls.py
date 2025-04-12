from django.urls import re_path
from .consumers import ChatConsumer
from django.urls import path
from .views import (
    ChannelView,
    InvitationCreateView,
    ChannelConnectView,
    MessageView
)
from rest_framework.routers import DefaultRouter
from .views import ChannelView, MessageView

router = DefaultRouter()
router.register('channels', ChannelView, basename='channels')
router.register('channels/<uuid:channel_uuid>/messages', MessageView, basename='messages')
urlpatterns = router.urls

websocket_urlpatterns = [
    #re_path(r'ws/chat/(?P<room_code>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', ChatConsumer.as_asgi()),
]

urlpatterns += [
    path('channels/<uuid:channel_uuid>/create_invitation/', InvitationCreateView.as_view(), name='invitation-create'),
    path('channels/<uuid:channel_uuid>/connect/<uuid:invitation_uuid>/', ChannelConnectView.as_view(), name='channel-connect'),
]