import hmac
import traceback
from time import time
from contextlib import suppress
from json import decoder, dumps, loads
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from bot import models
from bot.handlers import bot, utils
from bot.types import Media
from emoji import emojize
from telebot.types import Update


def payment_handler(request):
    _time = int(time())
    data = loads(request.body)
    reference = data.get('orderReference')
    user_id = int(reference.split('_')[1])
    str_signature = f'{reference};accept;{_time}'
    sign = hmac.new(settings.WAY_FOR_PAY_SECRET.encode('utf-8'), str_signature.encode('utf-8'), 'MD5').hexdigest()
    response = dumps({'orderReference': reference, 'status': 'accept', 'time': _time, 'signature': sign}).encode('utf-8')
    if data.get('transactionStatus') != 'Approved':
        return response
    amount = data.get('amount')
    currency = data.get('currency')
    try:
        user = models.User.objects.get(user_id=user_id)
    except models.User.DoesNotExist:
        return response
    models.Transaction.objects.create(user=user, amount=amount, currency=currency, reference=reference)
    try:
        orders_amount = models.Price.objects.get(price__range=[amount - 10 if amount > 10 else 0, amount + 10]).amount
    except models.Price.DoesNotExist:
        return response
    user.balance += orders_amount
    user.save()
    with suppress(Exception):
        bot.send_message(user.user_id, user.text('balance_top_upped').format(amount=orders_amount))
    return response


def portfolio_handler(request, portfolio_id):
    try:
        portfolio = models.Portfolio.objects.get(id=portfolio_id)
    except models.Portfolio.DoesNotExist:
        return HttpResponse(status=404)
    photo = [utils.get_file_url(file) for file in models.Media.objects.filter(portfolio=portfolio, type=Media.PHOTO)]
    video = [utils.get_file_url(file) for file in models.Media.objects.filter(portfolio=portfolio, type=Media.VIDEO)]
    media = {'photo': photo, 'video': video}
    return render(request, 'webview/portfolio.html', {'media': media, 'text': emojize(portfolio.text or '')})


@csrf_exempt
def update(request):
    try:
        update_json = Update.de_json(request.body.decode())
    except decoder.JSONDecodeError:
        return HttpResponse(b'JSON decode error', status=400)
    # noinspection PyBroadException
    try:
        bot.process_new_updates([update_json])
    except Exception:
        with suppress(Exception):
            bot.send_message(settings.DEVS[0], traceback.format_exc())
    return HttpResponse()


@csrf_exempt
def payment_callback(request):
    response = utils.exec_protected(payment_handler, request)
    return HttpResponse(response)


@csrf_exempt
def portfolio_webview(request, portfolio_id):
    response = utils.exec_protected(portfolio_handler, request, portfolio_id)
    return response
