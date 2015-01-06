# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GameXO',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(max_length=150)),
                ('active', models.BooleanField(default=True)),
                ('last_move_id', models.IntegerField(default=0)),
                ('winner_id', models.IntegerField(default=0)),
                ('users_state', models.CharField(default=b'["", ""]', max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InviteToGame',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('users', models.CharField(max_length=512)),
                ('game_started', models.BooleanField(default=False)),
                ('game_ended', models.BooleanField(default=False)),
                ('user_not_confirm_id', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserOnline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('online', models.BooleanField(default=False)),
                ('online_game', models.BooleanField(default=False)),
                ('dt', models.DateTimeField(auto_now=True)),
                ('game', models.ForeignKey(blank=True, to='mygame.GameXO', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='gamexo',
            name='invite',
            field=models.ForeignKey(to='mygame.InviteToGame'),
            preserve_default=True,
        ),
    ]
