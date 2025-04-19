import factory
from faker import Faker

from text_channels.models import Channel, ChannelMembership
from users.tests.factories import UserFactory

fake = Faker()


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
