import factory
from faker import Faker

from text_channels.models import Channel, ChannelBan, ChannelMembership
from users.tests.factories import UserFactory

fake = Faker('ru_RU')


class ChannelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Channel

    name = factory.declarations.LazyAttribute(lambda _: fake.word())
    owner = factory.declarations.SubFactory(UserFactory)


class ChannelMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChannelMembership

    user = factory.declarations.SubFactory(UserFactory)
    channel = factory.declarations.SubFactory(ChannelFactory)
    is_admin = False


class ChannelBanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChannelBan

    channel = factory.declarations.SubFactory(ChannelFactory)
    banned_by = factory.declarations.SubFactory(UserFactory)
    user = factory.declarations.SubFactory(UserFactory)
    reason = factory.declarations.LazyAttribute(lambda _: fake.paragraph())
