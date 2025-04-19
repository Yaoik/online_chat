import logging
from typing import cast
from uuid import UUID

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from invitations.tests.factories import InvitationFactory
from text_channels.models import Channel, ChannelMembership
from text_channels.serializers import ChannelMembershipSerializer, ChannelSerializer
from text_channels.tests.factories import ChannelFactory, ChannelMembershipFactory
from users.tests.factories import UserFactory

logger = logging.getLogger(__name__)


@pytest.fixture
def api_client() -> APIClient:
    client = APIClient()
    client.cookies.clear()
    return client


@pytest.fixture
def authenticated_client(api_client: APIClient, user: UserFactory) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user() -> UserFactory:
    return UserFactory()


@pytest.mark.django_db
class TestChannelView:
    def test_list_channels_authenticated(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse("channels-list")
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["uuid"] == str(channel.uuid)

    def test_create_channel_authenticated(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        url = reverse("channels-list")
        data = {"name": "Test Channel"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_201_CREATED
        channel = Channel.objects.get(uuid=response.data["uuid"])
        assert channel.name == "Test Channel"
        assert channel.owner == user
        assert ChannelMembership.objects.filter(
            user=user, channel=channel, is_admin=True
        ).exists()

    def test_retrieve_channel_authenticated(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse("channels-detail", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_200_OK
        serializer = ChannelSerializer(channel)
        assert response.data == serializer.data

    def test_update_channel_authenticated(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse("channels-detail", kwargs={"channel_uuid": channel.uuid})
        data = {"name": "Updated Channel"}
        response = cast(Response, authenticated_client.patch(url, data, format="json"))

        assert response.status_code == status.HTTP_200_OK
        channel.refresh_from_db()
        assert channel.name == "Updated Channel"

    def test_delete_channel_authenticated(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse("channels-detail", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Channel.objects.filter(uuid=channel.uuid).exists()

    def test_unauthenticated_access(self, api_client: APIClient) -> None:
        url = reverse("channels-list")
        response = cast(Response, api_client.get(url))
        api_client.cookies.clear()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_forbidden_access(self, authenticated_client: APIClient, user: UserFactory) -> None:
        channel = ChannelFactory()
        ChannelMembershipFactory(user=user, channel=channel, is_admin=False)
        url = reverse("channels-detail", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.patch(url, {"name": "Updated"}))

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestChannelConnectView:
    def test_connect_to_channel(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory()
        invitation = InvitationFactory(channel=channel)
        url = reverse(
            "channel-invitations-connect", kwargs={"invitation_uuid": invitation.uuid}
        )
        response = cast(Response, authenticated_client.post(url))

        assert response.status_code == status.HTTP_201_CREATED
        assert ChannelMembership.objects.filter(
            user=user, channel=channel
        ).exists()
        serializer = ChannelSerializer(channel)
        assert response.data == serializer.data

    def test_connect_with_expired_invitation(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory()
        invitation = InvitationFactory(channel=channel, expires_in=timezone.now())
        url = reverse(
            "channel-invitations-connect", kwargs={"invitation_uuid": invitation.uuid}
        )
        response = cast(Response, authenticated_client.post(url))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_connect_already_member(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory()
        invitation = InvitationFactory(channel=channel)
        ChannelMembershipFactory(user=user, channel=channel)
        url = reverse(
            "channel-invitations-connect", kwargs={"invitation_uuid": invitation.uuid}
        )
        response = cast(Response, authenticated_client.post(url))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Вы не можете подключиться в этот канал" in str(response.data)


@pytest.mark.django_db
class TestChannelDisconnectView:
    def test_disconnect_from_channel(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory()
        ChannelMembershipFactory(user=user, channel=channel)
        url = reverse(
            "channel-invitations-disconnect", kwargs={"channel_uuid": channel.uuid}
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ChannelMembership.objects.filter(
            user=user, channel=channel
        ).exists()

    def test_disconnect_non_member(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory()
        url = reverse(
            "channel-invitations-disconnect", kwargs={"channel_uuid": channel.uuid}
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_404_NOT_FOUND
