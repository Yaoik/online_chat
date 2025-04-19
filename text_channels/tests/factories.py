import factory
from factory.django import DjangoModelFactory
from faker import Faker

from text_channels.models import Channel, ChannelMembership
from users.models import User

fake = Faker()
