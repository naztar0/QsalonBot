# Generated by Django 4.0.1 on 2022-02-08 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_remove_settings_hint_media_id_portfolio_message_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaGroupHelper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media_group_id', models.PositiveBigIntegerField()),
                ('photo_id', models.CharField(default=None, max_length=128, null=True)),
                ('video_id', models.CharField(default=None, max_length=128, null=True)),
            ],
        ),
    ]
