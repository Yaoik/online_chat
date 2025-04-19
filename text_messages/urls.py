from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from .views import MessageView

urlpatterns = [
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
]
