import factory
from faker import Faker

from text_channels.tests.factories import ChannelFactory
from text_messages.models import Message
from users.tests.factories import UserFactory

fake = Faker('ru_RU')


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    user = factory.declarations.SubFactory(UserFactory)
    channel = factory.declarations.SubFactory(ChannelFactory)
    content = factory.declarations.LazyFunction(lambda: fake.paragraph())
