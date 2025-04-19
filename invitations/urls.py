from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import InvitationChannelPreviewView, InvitationView

urlpatterns = [
    path(
        'api/channels/<uuid:channel_uuid>/invitations/',
        InvitationView.as_view({'get': 'list', 'post': 'create'}),
        name='channel-invitations-list'
    ),
    path(
        'api/channels/<uuid:channel_uuid>/invitationas/<uuid:invitation_uuid>/',
        InvitationView.as_view({'delete': 'destroy', 'get': 'retrieve'}),
        name='channel-invitations-detail',
    ),
    path(
        'api/invitations/<uuid:invitation_uuid>/',
        InvitationChannelPreviewView.as_view(),
        name='channel-invitations-preview',
    ),
]
