from bot.handlers import bot
from django.core.management.base import BaseCommand
from app.settings import WEBHOOK_URL


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--lp')

    def handle(self, *args, **options):
        if options['lp']:
            bot.delete_webhook()
            bot.polling()
        else:
            bot.delete_webhook()
            bot.set_webhook(WEBHOOK_URL)
            print(bot.get_webhook_info())
