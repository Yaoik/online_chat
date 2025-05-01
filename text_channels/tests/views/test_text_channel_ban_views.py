import logging
from typing import cast

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from text_channels.models import Channel, ChannelBan, ChannelMembership
from text_channels.tests.factories import (
    ChannelBanFactory,
    ChannelFactory,
    ChannelMembershipFactory,
)
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


@pytest.fixture
def channel() -> Channel:
    return ChannelFactory()


@pytest.fixture
def admin_user() -> UserFactory:
    return UserFactory()


@pytest.fixture
def admin_membership(admin_user: UserFactory, channel: Channel) -> ChannelMembership:
    return ChannelMembershipFactory(user=admin_user, channel=channel, is_admin=True)


@pytest.fixture
def non_admin_user() -> UserFactory:
    return UserFactory()


@pytest.fixture
def non_admin_membership(non_admin_user: UserFactory, channel: Channel) -> ChannelMembership:
    return ChannelMembershipFactory(user=non_admin_user, channel=channel, is_admin=False)


@pytest.mark.django_db
class TestChannelBanView:
    def test_list_bans_authenticated_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        bans = ChannelBanFactory.create_batch(25, channel=channel, banned_by=user)
        url = reverse("channel-ban-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url))
        data: dict = response.data  # type: ignore
        assert response.status_code == status.HTTP_200_OK
        assert data["count"] == 25
        assert len(data["results"]) == 20
        assert data["next"] is not None
        assert data["previous"] is None

        first_ban = bans[0]
        assert data["results"][0]["uuid"] == str(first_ban.uuid)

    def test_list_bans_pagination_second_page(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        ChannelBanFactory.create_batch(25, channel=channel, banned_by=user)
        url = reverse("channel-ban-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url, {"page": 2}))
        data: dict = response.data  # type: ignore

        assert response.status_code == status.HTTP_200_OK
        assert data["count"] == 25
        assert len(data["results"]) == 5
        assert data["next"] is None
        assert data["previous"] is not None

    def test_create_ban_authenticated_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        banned_user = UserFactory()
        ChannelMembershipFactory(user=banned_user, channel=channel, is_admin=False)
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        data = {"reason": "Spamming"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))
        data: dict = response.data  # type: ignore

        assert response.status_code == status.HTTP_201_CREATED
        ban = ChannelBan.objects.get(uuid=data["uuid"])
        assert ban.user == banned_user
        assert ban.banned_by == user
        assert ban.channel == channel
        assert ban.reason == "Spamming"
        assert not ChannelMembership.objects.filter(user=banned_user, channel=channel).exists()

    def test_create_ban_self(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        url = reverse(
            "channel-ban-detail",
            kwargs={
                "channel_uuid": channel.uuid,
                "user_id": user.id,  # type: ignore
            },
        )
        data = {"reason": "Self-ban"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Нельза забанить себя" in str(response.data)

    def test_create_ban_non_member(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        banned_user = UserFactory()  # Не в канале
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        data = {"reason": "Not allowed"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Пользователь не в канале или админ" in str(response.data)

    def test_create_ban_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        banned_user = UserFactory()
        ChannelMembershipFactory(user=banned_user, channel=channel, is_admin=True)
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        data = {"reason": "Admin ban"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Пользователь не в канале или админ" in str(response.data)

    def test_create_ban_invalid_reason(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        banned_user = UserFactory()
        ChannelMembershipFactory(user=banned_user, channel=channel, is_admin=False)
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        data = {"reason": "A" * 256}  # Слишком длинная причина
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "max_length" in str(response.data)

    def test_delete_ban_authenticated_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=True)
        banned_user = UserFactory()
        ban = ChannelBanFactory(channel=channel, user=banned_user, banned_by=user)
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ChannelBan.objects.filter(uuid=ban.uuid).exists()

    def test_list_bans_non_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=False)
        url = reverse("channel-ban-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, authenticated_client.get(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_ban_non_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=False)
        banned_user = UserFactory()
        ChannelMembershipFactory(user=banned_user, channel=channel, is_admin=False)
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        data = {"reason": "Spamming"}
        response = cast(Response, authenticated_client.post(url, data, format="json"))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_ban_non_admin(
        self,
        authenticated_client: APIClient,
        user: UserFactory,
        channel: Channel,
    ) -> None:
        ChannelMembershipFactory(user=user, channel=channel, is_admin=False)
        banned_user = UserFactory()
        ChannelBanFactory(channel=channel, user=banned_user)
        url = reverse(
            "channel-ban-detail",
            kwargs={"channel_uuid": channel.uuid, "user_id": banned_user.id},
        )
        response = cast(Response, authenticated_client.delete(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_access(self, api_client: APIClient, channel: Channel) -> None:
        url = reverse("channel-ban-list", kwargs={"channel_uuid": channel.uuid})
        response = cast(Response, api_client.get(url))

        assert response.status_code == status.HTTP_403_FORBIDDEN
