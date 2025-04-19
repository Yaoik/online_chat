import logging
import uuid
from datetime import timedelta

import factory
import pytest
from chat.models import Channel, Invitation, Message
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from text_channels.models import ChannelMembership
from users.models import User

logger = logging.getLogger(__name__)

# Factory Boy для создания тестовых данных
fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.user_name())
    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.LazyAttribute(lambda _: fake.password())


class ChannelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Channel

    name = factory.LazyAttribute(lambda _: fake.word())
    owner = factory.SubFactory(UserFactory)


class ChannelMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChannelMembership

    user = factory.SubFactory(UserFactory)
    channel = factory.SubFactory(ChannelFactory)
    is_admin = False


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    uuid = factory.LazyFunction(uuid.uuid4)
    channel = factory.SubFactory(ChannelFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.LazyAttribute(lambda _: fake.text())


class InvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invitation

    author = factory.SubFactory(UserFactory)
    channel = factory.SubFactory(ChannelFactory)
    expiration_period = "24"
    expires_in = factory.LazyAttribute(lambda o: timezone.now() + timedelta(hours=int(o.expiration_period)))


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def channel(user):
    return ChannelFactory(owner=user)


@pytest.fixture
def channel_membership(user, channel):
    return ChannelMembershipFactory(user=user, channel=channel, is_admin=True)


@pytest.fixture
def message(channel_membership):
    return MessageFactory(channel=channel_membership.channel, user=channel_membership.user)


@pytest.mark.django_db
class TestChannelAPI:
    def test_create_channel(self, authenticated_client, user):
        url = reverse('channels-list')
        data = {'name': 'Test Channel'}
        response = authenticated_client.post(url, data, format='json')

        logger.info(f"Create channel response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert Channel.objects.count() == 1
        assert ChannelMembership.objects.filter(user=user, is_admin=True).exists()

    def test_list_channels(self, authenticated_client, channel_membership):
        url = reverse('channels-list')
        response = authenticated_client.get(url)

        logger.info(f"List channels response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1  # Учитываем пагинацию

    def test_non_member_cannot_access_channel(self, authenticated_client, channel):
        url = reverse('channels-detail', kwargs={'channel_uuid': channel.uuid})
        response = authenticated_client.get(url)

        logger.info(f"Non-member channel access response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMessageAPI:
    def test_create_message(self, authenticated_client, channel_membership):
        channel = channel_membership.channel
        url = reverse('channel-messages-list', kwargs={'channel_uuid': channel.uuid})
        data = {'content': 'Hello, world!'}
        response = authenticated_client.post(url, data, format='json')

        logger.info(f"Create message response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert Message.objects.count() == 1
        assert Message.objects.first().content == 'Hello, world!'

    def test_non_member_cannot_create_message(self, authenticated_client, channel):
        url = reverse('channel-messages-list', kwargs={'channel_uuid': channel.uuid})
        data = {'content': 'Hello, world!'}
        response = authenticated_client.post(url, data, format='json')

        logger.info(f"Non-member create message response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_messages(self, authenticated_client, channel_membership, message):
        channel = channel_membership.channel
        url = reverse('channel-messages-list', kwargs={'channel_uuid': channel.uuid})
        response = authenticated_client.get(url)

        logger.info(f"List messages response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1  # Учитываем пагинацию


@pytest.mark.django_db
class TestInvitationAPI:
    def test_create_invitation(self, authenticated_client, channel_membership):
        channel = channel_membership.channel
        url = reverse('channel-invitations-list', kwargs={'channel_uuid': channel.uuid})
        data = {'expiration_period': '24'}
        response = authenticated_client.post(url, data, format='json')

        logger.info(f"Create invitation response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        assert Invitation.objects.count() == 1

    def test_non_admin_cannot_create_invitation(self, authenticated_client, channel):
        ChannelMembershipFactory(user=authenticated_client.handler._force_user, channel=channel, is_admin=False)
        url = reverse('channel-invitations-list', kwargs={'channel_uuid': channel.uuid})
        data = {'expiration_period': '24'}
        response = authenticated_client.post(url, data, format='json')

        logger.info(f"Non-admin create invitation response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_connect_to_channel(self, authenticated_client, channel, user):
        invitation = InvitationFactory(channel=channel, author=user, expiration_period='24')
        url = reverse('channel-invitations-accept', kwargs={'invitation_uuid': invitation.token})
        response = authenticated_client.post(url, format='json')

        logger.info(f"Connect to channel response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_200_OK
        assert ChannelMembership.objects.filter(user=authenticated_client.handler._force_user, channel=channel).exists()

    def test_connect_with_expired_invitation(self, authenticated_client, channel, user):
        invitation = InvitationFactory(
            channel=channel,
            author=user,
            expiration_period='1',
            expires_in=timezone.now() - timedelta(hours=1)
        )
        url = reverse('channel-invitations-accept', kwargs={'invitation_uuid': invitation.token})
        response = authenticated_client.post(url, format='json')

        logger.info(f"Connect with expired invitation response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPermissions:
    def test_only_author_or_admin_can_edit_message(self, authenticated_client, channel_membership, message):
        other_user = UserFactory()
        message.user = other_user
        message.save()

        url = reverse('channel-messages-detail',
                      kwargs={'channel_uuid': channel_membership.channel.uuid, 'message_uuid': message.uuid})
        data = {'content': 'Edited message'}
        response = authenticated_client.patch(url, data, format='json')  # Заменили put на patch

        logger.info(f"Author or admin edit message response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_200_OK

    def test_non_author_non_admin_cannot_edit_message(self, authenticated_client, channel, message):
        non_member_user = UserFactory()
        authenticated_client.force_authenticate(user=non_member_user)

        if not ChannelMembership.objects.filter(user=non_member_user, channel=channel).exists():
            ChannelMembershipFactory(user=non_member_user, channel=channel, is_admin=False)

        url = reverse('channel-messages-detail', kwargs={'channel_uuid': channel.uuid, 'message_uuid': message.uuid})
        data = {'content': 'Edited message'}
        response = authenticated_client.patch(url, data, format='json')  # Заменили put на patch

        logger.info(f"Non-author non-admin edit message response: {response.status_code}, {response.data}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
