import logging
from typing import cast
from uuid import UUID

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from text_channels.models import Channel, ChannelMembership
from text_channels.tests.factories import ChannelFactory, ChannelMembershipFactory
from text_messages.models import Message
from text_messages.serializers import MessageSerializer
from text_messages.tests.factories import MessageFactory
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


@pytest.fixture
def channel() -> Channel:
    return ChannelFactory()


@pytest.fixture
def channel_membership(user: UserFactory, channel: Channel) -> ChannelMembership:
    return ChannelMembershipFactory(user=user, channel=channel, is_admin=False)


@pytest.mark.django_db
class TestMessageView:
    def test_list_messages_authenticated(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        messages = [MessageFactory(channel=channel, user=user) for _ in range(25)]
        url = reverse("channel-messages-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 25  # type: ignore
        assert len(response.data["results"]) == 20  # type: ignore
        assert response.data["next"] is not None  # type: ignore
        assert response.data["previous"] is None  # type: ignore

        first_message = messages[-1]
        assert response.data["results"][0]["uuid"] == str(first_message.uuid)  # type: ignore

    def test_list_messages_pagination_second_page(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        MessageFactory.create_batch(25, channel=channel, user=user)
        url = reverse("channel-messages-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url, {"page": 2}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 25  # type: ignore
        assert len(response.data["results"]) == 5  # type: ignore
        assert response.data["next"] is None  # type: ignore
        assert response.data["previous"] is not None  # type: ignore

    def test_create_message_authenticated(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        url = reverse("channel-messages-list", kwargs={"channel_uuid": channel.uuid})
        data = {"content": "Test message"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_201_CREATED
        message = Message.objects.get(uuid=response.data["uuid"])  # type: ignore
        assert message.content == "Test message"
        assert message.user == user
        assert message.channel == channel

    def test_retrieve_message_authenticated(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        message = MessageFactory(channel=channel, user=user)
        url = reverse(
            "channel-messages-detail",
            kwargs={"channel_uuid": channel.uuid, "message_uuid": message.uuid},
        )
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_200_OK
        serializer = MessageSerializer(message)
        assert response.data == serializer.data

    def test_update_message_by_author(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        message = MessageFactory(channel=channel, user=user)
        url = reverse(
            "channel-messages-detail",
            kwargs={"channel_uuid": channel.uuid, "message_uuid": message.uuid},
        )
        data = {"content": "Updated message"}
        response = cast(Response, authenticated_client.patch(url, data, format="json"))

        assert response.status_code == status.HTTP_200_OK
        message.refresh_from_db()
        assert message.content == "Updated message"

    def test_update_message_by_non_author(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        other_user = UserFactory()
        message = MessageFactory(channel=channel, user=other_user)
        url = reverse(
            "channel-messages-detail",
            kwargs={"channel_uuid": channel.uuid, "message_uuid": message.uuid},
        )
        data = {"content": "Updated message"}
        response = cast(Response, authenticated_client.patch(url, data, format="json"))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only edit your own messages" in str(response.data)

    def test_delete_message_by_author(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        message = MessageFactory(channel=channel, user=user)
        url = reverse(
            "channel-messages-detail",
            kwargs={"channel_uuid": channel.uuid, "message_uuid": message.uuid},
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Message.objects.filter(uuid=message.uuid).exists()

    def test_delete_message_by_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        other_user = UserFactory()
        message = MessageFactory(channel=channel, user=other_user)
        url = reverse(
            "channel-messages-detail",
            kwargs={"channel_uuid": channel.uuid, "message_uuid": message.uuid},
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Message.objects.filter(uuid=message.uuid).exists()

    def test_delete_message_by_non_author_non_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
        channel_membership: ChannelMembership,
    ) -> None:
        other_user = UserFactory()
        message = MessageFactory(channel=channel, user=other_user)
        url = reverse(
            "channel-messages-detail",
            kwargs={"channel_uuid": channel.uuid, "message_uuid": message.uuid},
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You can only delete your own messages or if you are a channel admin" in str(
            response.data
        )

    def test_access_by_non_member(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        url = reverse("channel-messages-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You are not a member of this channel or you are banned" in str(response.data)

    def test_access_by_banned_member(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_baned=True)
        url = reverse("channel-messages-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You are not a member of this channel or you are banned" in str(response.data)

    def test_unauthenticated_access(self, api_client: APIClient, channel: Channel) -> None:
        url = reverse("channel-messages-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, api_client.get(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN
