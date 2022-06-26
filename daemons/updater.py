from os import environ
from time import sleep
from contextlib import suppress
from datetime import timedelta
from django import setup
from django.utils import timezone


def update_active_clients():
    now = timezone.now()
    orders = models.Order.objects.filter(created__lte=now - timedelta(days=2), master__isnull=True, client__transaction__refund=True)
    for order in orders:
        if models.Request.objects.filter(order=order).count():
            continue
        refund_transactions(order.client)
        with suppress(Exception):
            bot.send_message(order.client.user_id, order.client.text('client_refunded'))


def main():
    executable = (update_active_clients,)
    while True:
        for exe in executable:
            exec_protected(exe)
        sleep(60)


if __name__ == '__main__':
    import sys
    sys.path.append('.')
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    setup()
    from bot import models
    from bot.misc import bot
    from bot.utils import exec_protected, refund_transactions, distinct
    main()
