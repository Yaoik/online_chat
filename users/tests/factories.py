import factory
from faker import Faker

from users.models import User

fake = Faker('ru_RU')


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.declarations.LazyAttribute(lambda _: fake.user_name())
    email = factory.declarations.LazyAttribute(lambda _: fake.email())
    password = factory.declarations.LazyAttribute(lambda _: fake.password())
