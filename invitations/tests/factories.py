import factory
from faker import Faker

from invitations.choices import ExpirationTimeChoices
from invitations.models import Invitation
from text_channels.tests.factories import ChannelFactory
from users.tests.factories import UserFactory

fake = Faker()


class InvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invitation

    author = factory.declarations.SubFactory(UserFactory)
    channel = factory.declarations.SubFactory(ChannelFactory)
    expiration_period = ExpirationTimeChoices.ONE_DAY
