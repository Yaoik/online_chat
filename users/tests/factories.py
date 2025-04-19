import factory
from factory.django import DjangoModelFactory
from faker import Faker

from text_channels.models import Channel, ChannelMembership
from users.models import User

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.user_name())
    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.LazyAttribute(lambda _: fake.password())
