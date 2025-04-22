import random
from datetime import datetime, timedelta

import factory
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from text_channels.models import Channel
from text_messages.models import Message
from users.models import User


class Command(BaseCommand):
    help = 'Генерация Message с русским текстом'

    def add_arguments(self, parser):
        parser.add_argument(
            '--total',
            type=int,
            required=True,
            help='Количество сообщений для создания'
        )
        parser.add_argument(
            '--i_do_not_use_it_in_the_prod',
            type=str,
            required=True,
            help='НЕ ИСПОЛЬЗОВАТЬ В ПРОДАКШЕНЕ, ЭТО ТОЛЬКО ДЛЯ РАЗРАБОТКИ. Для использования команды передать \"i_understand\"'
        )

    def handle(self, *args, **kwargs):
        if kwargs['i_do_not_use_it_in_the_prod'] != 'i_understand':
            self.stdout.write(self.style.ERROR('Не подтверждено использование команды'))
            return

        fake = Faker('ru_RU')
        total = kwargs['total']

        users = list(User.objects.all().only('id'))
        channels = list(Channel.objects.all().only('id'))

        if not users or not channels:
            self.stdout.write(self.style.ERROR('Нет пользователей или каналов!'))
            return

        same_user_chance = 0.7
        short_message_chance = 0.1
        change_channel_chance = 0.1
        update_chance = 0.1
        change_date_chance = 0.2

        end_date = timezone.now()
        start_date = end_date - timedelta(days=random.randint(1, 365*3))

        current_user = random.choice(users)
        current_channel = random.choice(channels)
        created_at = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        for _ in range(total):
            if short_message_chance > random.random():
                content = f'{fake.text(max_nb_chars=20)}'
            else:
                content = f'{fake.paragraph()}'
            if change_date_chance > random.random():
                created_at = start_date + timedelta(
                    seconds=random.randint(0, int((end_date - start_date).total_seconds()))
                )
            else:
                created_at += timedelta(seconds=random.randint(1, 180))
            if same_user_chance > random.random():
                current_user = random.choice(users)
            if change_channel_chance > random.random():
                current_channel = random.choice(channels)
            if update_chance > random.random():
                updated_at = created_at + timedelta(minutes=random.randint(1, 455))
            else:
                updated_at = created_at
            message = Message.objects.create(
                user=current_user,
                channel=current_channel,
                content=content,
                created_at=created_at,
                updated_at=updated_at,
            )
            Message.objects.filter(uuid=message.uuid).update(created_at=created_at, updated_at=updated_at)

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {total} сообщений')
        )
