import json
from datetime import datetime
from contextlib import suppress
from telebot import types
from telebot.apihelper import ApiTelegramException
from bot import utils, misc, models
from bot.misc import bot
from bot.utils import ButtonSet, answer
from bot.types import Log, User, Media
from bot.utils_lib import emoji


@bot.message_handler(commands=['start'])
@utils.user_handler
@utils.logger_middleware(Log.COMMAND)
def start_handler(message: types.Message, user: models.User):
    user.reset_state()
    answer(message, user.text('start_choose'), reply_markup=ButtonSet(ButtonSet.START))


@bot.message_handler(commands=['_master'])
@utils.user_handler
def start_handler(message: types.Message, user: models.User):
    user.type = User.MASTER
    user.save()
    answer(message, 'Now you are the master')


@bot.message_handler(commands=['_client'])
@utils.user_handler
def start_handler(message: types.Message, user: models.User):
    user.type = User.CLIENT
    user.save()
    answer(message, 'Now you are the client')


@bot.message_handler(content_types=['text'])
@utils.user_handler
def distribute_state_text_handler(message: types.Message, user: models.User):
    if not user.state:
        main_text_handler(message, user)
        return
    state_funcs = {
        utils.States.SUBSCRIPTIONS: save_categories,
        utils.States.PORTFOLIO_TEXT: portfolio_set_text,
        utils.States.PORTFOLIO_MEDIA: portfolio_set_media,
        utils.States.NEW_ORDER_CATEGORY: client_no_text,
        utils.States.NEW_ORDER_DATE: client_no_text,
        utils.States.NEW_ORDER_TIME: client_no_text,
        utils.States.NEW_ORDER_FORM_TEXT_MEDIA: client_text_media,
    }
    if state_funcs.get(user.state):
        state_funcs[user.state](message, user)
    else:
        main_text_handler(message, user)


@bot.message_handler(content_types=['photo', 'video', 'document', 'animation'])
@utils.user_handler
def media_handler(message: types.Message, user: models.User):
    state_funcs = {
        utils.States.PORTFOLIO_MEDIA: utils.media_extractor,
        utils.States.NEW_ORDER_FORM_TEXT_MEDIA: utils.media_extractor
    }
    if state_funcs.get(user.state):
        state_funcs[user.state](message, user)
    else:
        answer(message, user.text('unknown_action'))


@bot.message_handler(content_types=['location'])
@utils.user_handler
def distribute_state_location_handler(message: types.Message, user: models.User):
    if not user.state:
        main_text_handler(message, user)
        return
    state_funcs = {
        utils.States.NEW_LOCATION: save_location,
        utils.States.NEW_ORDER_LOCATION: client_location,
    }
    if state_funcs.get(user.state):
        state_funcs[user.state](message, user)


@bot.callback_query_handler(lambda callback: True)
@utils.user_handler
def callback_handler(callback: types.CallbackQuery, user: models.User):
    data = utils.get_callback(callback.data)
    if data is None:
        return
    func, data = data
    callback_funcs = {
        utils.CallbackFuncs.MASTER_CATEGORIES: master_subcategories,
        utils.CallbackFuncs.CHOOSE_CATEGORY: master_choose_category,
        utils.CallbackFuncs.CHOOSE_SUBCATEGORY: master_change_categories,
        utils.CallbackFuncs.MASTER_PRICE: master_pay,
        utils.CallbackFuncs.NEW_ORDER_CHOOSE_CATEGORY: client_choose_category,
        utils.CallbackFuncs.NEW_ORDER_CATEGORIES: client_choose_category,
        utils.CallbackFuncs.NEW_ORDER_SUBCATEGORIES: client_choose_subcategory,
        utils.CallbackFuncs.CHOOSE_DAY: client_choose_day,
        utils.CallbackFuncs.CHOOSE_TIME: client_choose_time,
        utils.CallbackFuncs.CHOOSE_TIME_SUBMIT: client_submit_time,
        utils.CallbackFuncs.CHOOSE_PRICE: client_choose_price,
        utils.CallbackFuncs.CHOOSE_PRICE_SUBMIT: client_submit_price,
        utils.CallbackFuncs.MASTER_ACCEPT_ORDER: master_accept_order,
        utils.CallbackFuncs.CLIENT_ACCEPT_ORDER: client_accept_order,
        utils.CallbackFuncs.ORDER_INFO: order_info,
        utils.CallbackFuncs.ORDER_DELETE: order_delete,
        utils.CallbackFuncs.ORDER_REQUESTS_AMOUNT: order_requests_amount
    }
    if callback_funcs.get(func):
        callback_funcs[func](callback.message, callback, user, data)


def main_text_handler(message: types.Message, user):
    if message.text == misc.back_button:
        user.reset_state()
        answer(message, user.text('start_choose'), reply_markup=ButtonSet(ButtonSet.START))
    if message.text == misc.role_buttons[0]:
        register_client(message, user)
    elif message.text == misc.role_buttons[1]:
        register_master(message, user)
    elif message.text == misc.master_buttons_1[0]:
        orders_history(message, user)
    elif message.text == misc.master_buttons_1[1]:
        answer(message, user.text('master_profile'), reply_markup=ButtonSet(ButtonSet.MASTER_2))
    elif message.text == misc.master_buttons_1[2]:
        master_balance(message, user)
    elif message.text == misc.master_buttons_2[0]:
        master_categories(message, user)
    elif message.text == misc.master_buttons_2[1]:
        master_portfolio(message, user)
    elif message.text == misc.master_buttons_2[2]:
        master_location(message, user)
    elif message.text == misc.master_buttons_2[3]:
        answer(message, user.text('start_master'), reply_markup=ButtonSet(ButtonSet.MASTER_1))
    elif message.text in misc.edit_buttons:
        edit_portfolio(message, user)
    elif message.text == misc.client_buttons[0]:
        client_create_order(message, user)
    elif message.text == misc.client_buttons[1]:
        orders_history(message, user)


@utils.logger_middleware(Log.REPLY_BUTTON)
def register_client(message: types.Message, user):
    user.type = User.CLIENT
    user.save()
    answer(message, user.text('start_client'), reply_markup=ButtonSet(ButtonSet.CLIENT))


@utils.logger_middleware(Log.REPLY_BUTTON)
def register_master(message: types.Message, user: models.User):
    user.type = User.MASTER
    user.save()
    if not user.is_active_master:
        if not user.categories.count():
            answer(message, user.text('start_master_steps'))
            answer(message, user.text('step_n').format(n=1))
            user.update_state_data({'register': True})
            master_categories(message, user)
        elif not user.location.x:
            answer(message, user.text('step_n').format(n=2))
            user.update_state_data({'register': True})
            master_location(message, user)
        elif not user.portfolio:
            user.update_state_data({'register': True})
            edit_portfolio(message, user)
        else:
            user.is_active_master = True
            user.save()
            answer(message, user.text('start_master'), reply_markup=ButtonSet(ButtonSet.MASTER_1))
    else:
        answer(message, user.text('start_master'), reply_markup=ButtonSet(ButtonSet.MASTER_1))


def master_categories(message, user, edit=False):
    cats = {}
    for cat in models.Category.objects.all():
        cats[cat.id] = [cat.title, user.categories.filter(category_id__exact=cat.id).count()]
    if edit:
        bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=ButtonSet(ButtonSet.INL_MASTER_CATEGORIES, cats))
        return
    user.set_state(utils.States.SUBSCRIPTIONS)
    answer(message, user.text('subs_choosing'), reply_markup=ButtonSet(ButtonSet.SAVE_CHANGES))
    answer(message, user.text('cats_choose'), reply_markup=ButtonSet(ButtonSet.INL_MASTER_CATEGORIES, cats))


def master_location(message, user):
    if not user.get_state_data().get('register'):
        if not user.location.x:
            answer(message, user.text('location_not_set'))
        else:
            bot.send_location(message.chat.id, user.location.x, user.location.y)
    user.set_state(utils.States.NEW_LOCATION)
    answer(message, user.text('send_location'), reply_markup=ButtonSet(ButtonSet.SEND_LOCATION))


@utils.reset_state_checker('master_profile', ButtonSet.MASTER_2)
@utils.logger_middleware(Log.REPLY_BUTTON)
def save_categories(message, user: models.User):
    if message.text != misc.save_changes:
        return
    if user.get_state_data().get('register'):
        answer(message, user.text('step_n').format(n=2))
        master_location(message, user)
    else:
        user.reset_state()
        answer(message, user.text('categories_saved'), reply_markup=ButtonSet(ButtonSet.MASTER_2))


@utils.reset_state_checker('master_profile', ButtonSet.MASTER_2)
@utils.logger_middleware(Log.REPLY_BUTTON)
def save_location(message, user: models.User):
    user.city = utils.get_city(message.location.latitude, message.location.longitude)
    user.location.x, user.location.y = message.location.latitude, message.location.longitude
    user.is_active_master = True
    user.save()
    if user.get_state_data().get('register'):
        answer(message, user.text('master_registered_demo'), reply_markup=ButtonSet(ButtonSet.MASTER_2))
        edit_portfolio(message, user)
    else:
        user.reset_state()
        answer(message, user.text('location_saved'), reply_markup=ButtonSet(ButtonSet.MASTER_2))


def save_portfolio(message, user: models.User):
    data = user.get_state_data()
    media = utils.media_group_collector(data)
    if not media:
        answer(message, "Отправьте хотя-бы один медиа файл!")
        return
    if user.portfolio:
        if data.get('only_text'):
            media.photo = json.loads(user.portfolio.photo)
            media.video = json.loads(user.portfolio.video)
        elif data.get('only_media'):
            media.text = user.portfolio.text
        user.portfolio.delete()
    user.portfolio = models.Portfolio.objects.create(text=media.text)
    user.save()
    photos = [{'file_id': file.file_id, 'type': Media.PHOTO, 'portfolio': user.portfolio} for file in media.photo]
    videos = [{'file_id': file.file_id, 'type': Media.VIDEO, 'portfolio': user.portfolio} for file in media.video]
    models.Media.objects.bulk_create(photos + videos)
    user.reset_state()
    answer(message, user.text('master_registered_completely') if data.get('register') else user.text('saved'), reply_markup=ButtonSet(ButtonSet.MASTER_2))


@utils.reset_state_checker('start_master', ButtonSet.MASTER_1)
def master_portfolio(message, user: models.User):
    if user.portfolio:
        utils.send_media_group(message.chat.id, utils.MediaGroup(user.portfolio))
        answer(message, user.text('portfolio_above'), reply_markup=ButtonSet(ButtonSet.EDIT_PORTFOLIO))
    else:
        answer(message, user.text('portfolio_not_set'), reply_markup=ButtonSet(ButtonSet.CREATE))


@utils.reset_state_checker('master_profile', ButtonSet.MASTER_2)
def edit_portfolio(message, user: models.User):
    if user.get_state_data().get('register'):
        answer(message, user.text('step_n').format(n=3))
    if message.text == misc.edit_buttons[1]:
        user.update_state_data({'only_text': True})
    elif message.text == misc.edit_buttons[2]:
        user.set_state(utils.States.PORTFOLIO_MEDIA)
        user.update_state_data({'only_media': True})
        answer(message, user.text('send_portfolio_media'), reply_markup=ButtonSet(ButtonSet.NEXT, row_width=2))
        return
    user.set_state(utils.States.PORTFOLIO_TEXT)
    answer(message, user.text('send_portfolio_text'), reply_markup=ButtonSet(ButtonSet.BACK))


@utils.reset_state_checker('master_profile', ButtonSet.MASTER_2)
def portfolio_set_text(message: types.Message, user: models.User):
    if len(message.text) > 1000:
        answer(message, user.text('text_too_long'))
        return
    user.update_state_data({'text': emoji.demojize(message.text)})
    if user.get_state_data().get('only_text'):
        save_portfolio(message, user)
        return
    if user.get_state_data().get('register'):
        answer(message, user.text('step_n').format(n=4))
    user.set_state(utils.States.PORTFOLIO_MEDIA)
    answer(message, user.text('send_portfolio_media'), reply_markup=ButtonSet(ButtonSet.NEXT, row_width=2))


@utils.reset_state_checker('master_profile', ButtonSet.MASTER_2)
def portfolio_set_media(message: types.Message, user: models.User):
    if message.text == misc.next_button:
        save_portfolio(message, user)
    else:
        answer(message, user.text('unknown_action'))


@utils.logger_middleware(Log.REPLY_BUTTON)
def master_balance(message, user: models.User):
    info = ''
    if user.categories.count() == 0:
        info = user.text('master_balance_subscribe')
    buttons = [(x.price, x.amount) for x in models.Price.objects.all()]
    answer(message, user.text('master_balance').format(balance=user.balance, info=info), reply_markup=ButtonSet(ButtonSet.INL_MASTER_PRICES, buttons))


@utils.reset_state_checker('start_client', ButtonSet.CLIENT)
def client_no_text(message, user: models.User):
    answer(message, user.text('unknown_action'))


@utils.logger_middleware(Log.REPLY_BUTTON)
def client_create_order(message, user):
    user.set_state(utils.States.NEW_ORDER_CATEGORY)
    answer(message, user.text('step_n_m').format(n=1, m=5), reply_markup=ButtonSet(ButtonSet.BACK))
    cats = {cat.id: cat.title for cat in models.Category.objects.all()}
    answer(message, user.text('order_cats'), reply_markup=ButtonSet(ButtonSet.INL_CLIENT_CATEGORIES, cats))


@utils.reset_state_checker('start_client', ButtonSet.CLIENT)
def client_location(message: types.Message, user: models.User):
    x, y = message.location.latitude, message.location.longitude
    user.update_state_data({'x': x, 'y': y})
    user.set_state(utils.States.NEW_ORDER_DATE)
    answer(message, user.text('step_n_m').format(n=3, m=5), reply_markup=ButtonSet(ButtonSet.BACK))
    answer(message, user.text('order_date'), reply_markup=ButtonSet(ButtonSet.INL_CLIENT_DATE))


@utils.reset_state_checker('start_client', ButtonSet.CLIENT)
def client_text_media(message: types.Message, user: models.User):
    if message.text == misc.next_button:
        utils.save_order(user)
    if message.text:
        if len(message.text) > 600:
            answer(message, user.text('text_too_long'))
            return
        user.update_state_data({'text': message.text})
    else:
        answer(message, user.text('unknown_action'))


@utils.logger_middleware(Log.REPLY_BUTTON)
def orders_history(message: types.Message, user: models.User):
    if not user.type:
        return answer(message, user.text('orders_history_empty'))
    buttons = [[x.id, f"{x.subcategory.title} - {x.date.strftime('%d.%m')} в {', '.join(json.loads(x.times))}"]
               for x in models.Order.objects.filter(**{user.type.lower(): user}).order_by('-created')[:10]]
    answer(message, user.text('orders_history') if buttons else user.text('orders_history_empty'),
           reply_markup=ButtonSet(ButtonSet.INL_ORDERS_HISTORY, buttons))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def master_subcategories(message, callback: types.CallbackQuery, user: models.User, data):
    buttons = []
    for sub in models.Subcategory.objects.filter(category_id=data):
        sym = "✅ " if user.categories.filter(id=sub.id) else "❌ "
        buttons.append([sym + sub.title, {'sub_id': sub.id, 'cat_id': data}])
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=ButtonSet(ButtonSet.INL_MASTER_SUBCATEGORIES, buttons))


@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def master_change_categories(message, callback: types.CallbackQuery, user: models.User, data):
    cat = models.Subcategory.objects.get(id=data['sub_id'])
    if user.categories.filter(id=cat.id):
        user.categories.remove(cat)
    else:
        user.categories.add(cat)
    master_subcategories(message, callback, user, data['cat_id'])


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def master_choose_category(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    master_categories(message, user, True)


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def master_pay(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    pay_link = utils.way_for_pay_request_purchase(message.chat.id, data)
    if isinstance(pay_link, tuple):
        answer(message, f"Error: {pay_link[1]}", pm=False)
        return
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton("Оплатить", url=pay_link))
    with suppress(ApiTelegramException):
        bot.delete_message(message.chat.id, message.message_id)
    answer(message, user.text('master_pay').format(amount=models.Price.objects.get(price=data).amount), reply_markup=key)


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_choose_category(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    if data:
        buttons = [[x.title, x.id] for x in models.Subcategory.objects.filter(category_id=data)]
        with suppress(ApiTelegramException):
            bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ButtonSet(ButtonSet.INL_CLIENT_SUBCATEGORIES, buttons))
    else:
        cats = {cat.id: cat.title for cat in models.Category.objects.all()}
        with suppress(ApiTelegramException):
            bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=ButtonSet(ButtonSet.INL_CLIENT_CATEGORIES, cats))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_choose_subcategory(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    state_data = user.update_state_data({'sub_id': data})
    subcategory = models.Subcategory.objects.get(id=data)
    radius = subcategory.category.radius
    category_data = f'{subcategory.category.title} - {subcategory.title}'
    user.set_state(utils.States.NEW_ORDER_LOCATION)
    with suppress(ApiTelegramException):
        bot.delete_message(message.chat.id, message.message_id)
    answer(message, user.text('order_location').format(radius=radius, category=category_data), reply_markup=ButtonSet(ButtonSet.SEND_LOCATION))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_choose_day(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    if data == 0:
        now = datetime.now()
        if now.minute < 30:
            nearest = now.replace(minute=30)
        else:
            nearest = now.replace(hour=now.hour + 1 if now.hour < 23 else 0, minute=0)
        user.update_state_data({'date': nearest.timestamp(), "times": [nearest.strftime("%H:%M")]})
        user.set_state(utils.States.NEW_ORDER_TIME)
        client_submit_time(message, callback, user, data)
        return
    user.update_state_data({'date': data})
    user.set_state(utils.States.NEW_ORDER_TIME)
    with suppress(ApiTelegramException):
        bot.delete_message(message.chat.id, message.message_id)
    answer(message, user.text('order_time'), reply_markup=ButtonSet(ButtonSet.INL_CLIENT_TIME))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_choose_time(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    times = set(user.get_state_data().get('times', []))
    new = data not in times
    times.add(data) if new else times.remove(data)
    user.update_state_data({'times': sorted(times)})
    message.reply_markup.keyboard[misc.times.index(data) // 2][misc.times.index(data) % 2] = \
        types.InlineKeyboardButton(f"{'✅' if new else ''} {data}", callback_data=utils.set_callback(utils.CallbackFuncs.CHOOSE_TIME, data))
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=message.reply_markup)


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_submit_time(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    times = set(user.get_state_data().get('times', []))
    if not times:
        bot.answer_callback_query(callback.id, user.text('order_no_time'), show_alert=True)
        return
    user.set_state(utils.States.NEW_ORDER_PRICE)
    with suppress(ApiTelegramException):
        bot.delete_message(message.chat.id, message.message_id)
    args = ('' for _ in range(3))
    answer(message, user.text('order_price'), reply_markup=ButtonSet(ButtonSet.INL_PRICE, args))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_choose_price(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    price_flags = user.get_state_data().get('price') or 0
    price_flags ^= data
    user.update_state_data({'price': price_flags, 'photo': [], 'video': []})
    args = ('✅ ' if price_flags & 2 ** x else '' for x in range(3))
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=ButtonSet(ButtonSet.INL_PRICE, args))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_submit_price(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    if not user.get_state_data().get('price'):
        bot.answer_callback_query(callback.id, user.text('order_no_price'), show_alert=True)
        return
    user.set_state(utils.States.NEW_ORDER_FORM_TEXT_MEDIA)
    with suppress(ApiTelegramException):
        bot.delete_message(message.chat.id, message.message_id)
    answer(message, user.text('order_text_media'), reply_markup=ButtonSet(ButtonSet.NEXT, row_width=2))


@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def order_requests_amount(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    try:
        order = models.Order.objects.get(id=data)
    except models.Order.DoesNotExist:
        answer(message, user.text('client_canceled_order'), reply_to_message_id=message.message_id)
        return
    amount = models.Request.objects.filter(order=order).count()
    bot.answer_callback_query(callback.id, user.text('order_requests_count').format(amount=amount), True)


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def master_accept_order(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    if user.balance == 0:
        return answer(message, user.text('master_no_balance'))
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    try:
        order = models.Order.objects.get(id=data)
    except models.Order.DoesNotExist:
        return answer(message, user.text('client_canceled_order'), reply_to_message_id=message.message_id)
    if models.Request.objects.filter(order=order, master=user).count():
        return answer(message, user.text('master_order_exists'), reply_to_message_id=message.message_id)
    if order.master:
        return answer(message, user.text('client_has_master'), reply_to_message_id=message.message_id)
    try:
        bot.send_chat_action(order.client.user_id, 'typing')
    except ApiTelegramException:
        return answer(message, user.text('client_canceled_order'), reply_to_message_id=message.message_id)
    user.balance -= 1
    user.save()
    request = models.Request.objects.create(order=order, master=user, message_id=message.message_id)
    username = '@' + utils.esc_md(user.username) if user.username else ''
    address = utils.get_address(user.location.x, user.location.y, 'ru') or "недоступно"
    geolocation = f"https://maps.google.com/maps?q={user.location.x},{user.location.y}"
    bot.send_message(order.client.user_id, order.client.text('master_accepted_order')
                     .format(master_name=utils.esc_md(message.chat.first_name),
                             master_id=message.chat.id, master_username=username,
                             address=utils.esc_md(address), geolocation=geolocation),
                     reply_markup=ButtonSet(ButtonSet.INL_CLIENT_ACCEPT_ORDER, request.id, user.portfolio.id), parse_mode='Markdown')
    username = '@' + utils.esc_md(order.client.username) if order.client.username else ''
    answer(message, user.text('master_accepted_order_reply').format(client_id=order.client.user_id, client_username=username))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def client_accept_order(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    try:
        request = models.Request.objects.get(id=data)
    except models.Request.DoesNotExist:
        return
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    order = request.order
    if not order:
        return
    order.master = request.master
    order.message_id = request.message_id
    order.save()
    with suppress(Exception):
        bot.send_message(order.client.user_id, order.client.text('client_refunded'))
    username = '@' + utils.esc_md(user.username) if user.username else ''
    with suppress(ApiTelegramException):
        bot.send_message(order.master.user_id, order.master.text('client_accepted_order')
                         .format(client_id=user.user_id, client_username=username), parse_mode='Markdown')
    username = '@' + utils.esc_md(order.master.username) if order.master.username else ''
    answer(message, order.master.text('client_accepted_order_reply').format(master_id=order.master.user_id, master_username=username))


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def order_info(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    try:
        order = models.Order.objects.get(id=data)
    except models.Order.DoesNotExist:
        return
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    if user.type == User.CLIENT:
        user_type = 'Мастер' if order.master else 'Мастер пока не найден'
        user_type_id = order.master.user_id if order.master else 0
    else:
        user_type = 'Клиент'
        user_type_id = order.client.user_id
    geolocation = f"https://maps.google.com/maps?q={order.location.x},{order.location.y}"
    answer(message, user.text('order_info').format(user_type=user_type, user_type_id=user_type_id, category=order.subcategory.category,
                                                   subcategory=order.subcategory, date=order.date.strftime('%d.%m'),
                                                   times=', '.join(json.loads(order.times)), geolocation=geolocation),
           reply_markup=ButtonSet(ButtonSet.INL_ORDER_DELETE, order.id),
           reply_to_message_id=order.message_id if user.type == User.MASTER else None,
           allow_sending_without_reply=True, disable_web_page_preview=True)


# noinspection PyUnusedLocal
@utils.logger_middleware(Log.INLINE_BUTTON, is_callback=True)
def order_delete(message: types.Message, callback: types.CallbackQuery, user: models.User, data):
    try:
        order = models.Order.objects.get(id=data)
    except models.Order.DoesNotExist:
        return
    with suppress(ApiTelegramException):
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    with suppress(ApiTelegramException):
        if user.type == User.CLIENT:
            if order.master:
                bot.send_message(order.master.user_id, order.master.text('client_deleted_order').format(client_id=user.user_id), parse_mode='Markdown')
        else:
            bot.send_message(order.client.user_id, order.master.text('master_deleted_order').format(master_id=user.user_id), parse_mode='Markdown')
    order.delete()
    answer(message, user.text('order_deleted'))
