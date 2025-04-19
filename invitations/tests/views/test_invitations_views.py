import logging
from typing import cast
from uuid import UUID

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from invitations.models import Invitation
from invitations.serializers import InvitationSerializer
from invitations.tests.factories import InvitationFactory
from text_channels.tests.factories import ChannelFactory, ChannelMembershipFactory
from users.tests.factories import UserFactory

logger = logging.getLogger(__name__)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user: UserFactory) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user() -> UserFactory:
    return UserFactory()


@pytest.mark.django_db
class TestInvitationView:
    def test_list_invitations(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        invitation = InvitationFactory(channel=channel, author=user)
        url = reverse(
            "channel-invitations-list", kwargs={"channel_uuid": channel.uuid}
        )
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1  # type: ignore
        assert response.data['results'][0]["uuid"] == str(invitation.uuid)  # type: ignore

    def test_create_invitation(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse(
            "channel-invitations-list", kwargs={"channel_uuid": channel.uuid}
        )
        data = {"expiration_period": "24"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_201_CREATED
        invitation = Invitation.objects.get(uuid=response.data["uuid"])  # type: ignore
        assert invitation.author == user
        assert invitation.channel == channel
        assert invitation.expiration_period == "24"

    def test_retrieve_invitation(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory()
        invitation = InvitationFactory(channel=channel)
        url = reverse(
            "channel-invitations-preview",
            kwargs={"invitation_uuid": invitation.uuid},
        )
        response = cast(Response, authenticated_client.get(url))
        assert response.status_code == status.HTTP_200_OK
        serializer = InvitationSerializer(invitation)
        assert response.data == serializer.data

    def test_delete_invitation(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        invitation = InvitationFactory(channel=channel, author=user)
        url = reverse(
            "channel-invitations-detail",
            kwargs={"channel_uuid": channel.uuid, "invitation_uuid": invitation.uuid},
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Invitation.objects.filter(uuid=invitation.uuid).exists()

    def test_create_invalid_expiration_period(
        self, authenticated_client: APIClient, user: UserFactory
    ) -> None:
        channel = ChannelFactory(owner=user)
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse(
            "channel-invitations-list", kwargs={"channel_uuid": channel.uuid}
        )
        data = {"expiration_period": "invalid"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "is not a valid choice." in str(response.data)

    def test_unauthenticated_access(self, api_client: APIClient) -> None:
        channel = ChannelFactory()
        url = reverse(
            "channel-invitations-list", kwargs={"channel_uuid": channel.uuid}
        )
        response = cast(Response, api_client.get(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN
