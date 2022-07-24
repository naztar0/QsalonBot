from os import environ
from time import sleep
from contextlib import suppress
from django import setup
from django.utils import timezone


def orders_survey():
    orders = models.Order.objects.filter(status=types.Order.WAIT, created__lte=timezone.now() - timezone.timedelta(hours=2),
                                         created__gt=timezone.now() - timezone.timedelta(hours=3))
    for order in orders:
        order.status = types.Order.CANCELED
        order.save()
        with suppress(Exception):
            bot.send_message(order.client.user_id, order.client.text('order_survey'), parse_mode='Markdown',
                             reply_markup=ButtonSet(ButtonSet.INL_ORDER_SURVEY, order.id))
        sleep(0.1)


def main():
    executable = (orders_survey,)
    while True:
        for exe in executable:
            exec_protected(exe)
        sleep(60)


if __name__ == '__main__':
    import sys
    sys.path.append('.')
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    setup()
    from bot.utils import exec_protected, ButtonSet
    from bot import models, types
    from bot.misc import bot
    main()
