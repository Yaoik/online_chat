# Generated by Django 5.1.7 on 2025-04-17 17:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('text_channels', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_channels', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='channelmembership',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='text_channels.channel'),
        ),
        migrations.AddField(
            model_name='channelmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='channelmembership',
            index=models.Index(fields=['user', 'channel'], name='text_channe_user_id_5584ff_idx'),
        ),
        migrations.AddConstraint(
            model_name='channelmembership',
            constraint=models.UniqueConstraint(fields=('user', 'channel'), name='user_channel_unique_together'),
        ),
    ]
