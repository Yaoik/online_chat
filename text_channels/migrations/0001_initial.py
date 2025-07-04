# Generated by Django 5.1.7 on 2025-04-17 17:35

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Канал',
                'verbose_name_plural': 'Каналы',
            },
        ),
        migrations.CreateModel(
            name='ChannelMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_admin', models.BooleanField(default=False, verbose_name='Администратор')),
                ('is_baned', models.BooleanField(default=False, verbose_name='Забанен')),
            ],
            options={
                'verbose_name': 'Членство в канале',
                'verbose_name_plural': 'Членства в каналах',
            },
        ),
    ]
