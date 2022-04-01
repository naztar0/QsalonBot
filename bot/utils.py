import json
import hmac
import traceback
import requests
from math import cos, radians
from time import sleep, time
from datetime import datetime, timedelta
from contextlib import suppress
from django.conf import settings
from django.db.models import Func, ExpressionWrapper, FloatField
from preferences import preferences
from telebot.types import ReplyKeyboardMarkup as RKM, InlineKeyboardMarkup as IKM
from telebot.types import KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, InputMediaVideo
from telebot.apihelper import ApiTelegramException
from bot.utils_lib import helper, callback_data, emoji
from bot import models, misc
from bot.types import User
from app.settings import OPENCAGE_KEY


class States(helper.Helper):
    mode = helper.HelperMode.lowercase
    NEW_ORDER_CATEGORY = helper.Item()
    NEW_ORDER_LOCATION = helper.Item()
    NEW_ORDER_DATE = helper.Item()
    NEW_ORDER_TIME = helper.Item()
    NEW_ORDER_PRICE = helper.Item()
    NEW_ORDER_FORM_TEXT_MEDIA = helper.Item()
    PORTFOLIO_TEXT = helper.Item()
    PORTFOLIO_MEDIA = helper.Item()
    NEW_LOCATION = helper.Item()
    SUBSCRIPTIONS = helper.Item()
    CLIENT_ORDER_INFO = helper.Item()


class CallbackFuncs:
    NEW_ORDER_CATEGORIES = 0x00
    NEW_ORDER_SUBCATEGORIES = 0x01
    NEW_ORDER_CHOOSE_CATEGORY = 0x02
    CLIENT_ACCEPT_ORDER = 0x03
    MASTER_ACCEPT_ORDER = 0x04
    MASTER_CATEGORIES = 0x05
    MASTER_PRICE = 0x06
    CHOOSE_SUBCATEGORY = 0x07
    CHOOSE_CATEGORY = 0x08
    CHOOSE_DAY = 0x09
    CHOOSE_TIME = 0x0a
    CHOOSE_TIME_SUBMIT = 0x0b
    CHOOSE_PRICE = 0x0c
    CHOOSE_PRICE_SUBMIT = 0x0d
    ORDER_INFO = 0x0e
    ORDER_DELETE = 0x0f
    ORDER_REQUESTS_AMOUNT = 0x10


class ReplyKeyboardMarkup(RKM):
    def __bool__(self):
        return bool(self.keyboard)


class InlineKeyboardMarkup(IKM):
    def __bool__(self):
        return bool(self.keyboard)


class ButtonSet(helper.Helper):
    mode = helper.HelperMode.lowercase
    REMOVE = helper.Item()
    START = helper.Item()
    BACK = helper.Item()
    CLIENT = helper.Item()
    MASTER_1 = helper.Item()
    MASTER_2 = helper.Item()
    SEND_LOCATION = helper.Item()
    SAVE_CHANGES = helper.Item()
    EDIT_PORTFOLIO = helper.Item()
    CREATE = helper.Item()
    NEXT = helper.Item()
    INL_CLIENT_ACCEPT_ORDER = helper.Item()
    INL_MASTER_ACCEPT_ORDER = helper.Item()
    INL_PRICE = helper.Item()
    INL_CLIENT_CATEGORIES = helper.Item()
    INL_CLIENT_SUBCATEGORIES = helper.Item()
    INL_CLIENT_DATE = helper.Item()
    INL_CLIENT_TIME = helper.Item()
    INL_MASTER_CATEGORIES = helper.Item()
    INL_MASTER_SUBCATEGORIES = helper.Item()
    INL_MASTER_PRICES = helper.Item()
    INL_ORDERS_HISTORY = helper.Item()
    INL_ORDER_DELETE = helper.Item()
    INL_ORDER_REQUESTS_AMOUNT = helper.Item()

    def __new__(cls, btn_set: helper.Item = None, args=None, row_width=1):
        if btn_set == cls.REMOVE:
            return ReplyKeyboardRemove()
        key = ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)
        ikey = InlineKeyboardMarkup(row_width=row_width)
        if btn_set == cls.BACK:
            key.add(KeyboardButton(misc.back_button))
        elif btn_set == cls.START:
            key.add(*(KeyboardButton(x) for x in misc.role_buttons))
        elif btn_set == cls.CLIENT:
            key.add(*(KeyboardButton(x) for x in misc.client_buttons))
            key.add(KeyboardButton(misc.back_button))
        elif btn_set == cls.MASTER_1:
            key.row_width = 2
            key.add(*(KeyboardButton(x) for x in misc.master_buttons_1))
            key.add(KeyboardButton(misc.back_button))
        elif btn_set == cls.MASTER_2:
            key.row_width = 3
            key.add(*(KeyboardButton(x) for x in misc.master_buttons_2))
        elif btn_set == cls.SAVE_CHANGES:
            key.add(*(KeyboardButton(x) for x in (misc.save_changes, misc.back_button)))
        elif btn_set == cls.EDIT_PORTFOLIO:
            key.add(*(KeyboardButton(x) for x in (*misc.edit_buttons, misc.back_button)))
        elif btn_set == cls.CREATE:
            key.add(*(KeyboardButton(x) for x in (misc.create_button, misc.back_button)))
        elif btn_set == cls.NEXT:
            key.add(*(KeyboardButton(x) for x in (misc.back_button, misc.next_button)))
        elif btn_set == cls.SEND_LOCATION:
            key.add(KeyboardButton('Отправить моё местоположение', request_location=True))
            key.add(KeyboardButton(misc.back_button))
        elif btn_set == cls.INL_CLIENT_ACCEPT_ORDER:
            ikey.add(InlineKeyboardButton('Согласиться', callback_data=set_callback(CallbackFuncs.CLIENT_ACCEPT_ORDER, args)))
        elif btn_set == cls.INL_MASTER_ACCEPT_ORDER:
            ikey.row_width = 2
            ikey.add(*(InlineKeyboardButton('Выполнить', callback_data=set_callback(CallbackFuncs.MASTER_ACCEPT_ORDER, args)),
                       InlineKeyboardButton('Кол-во откликов', callback_data=set_callback(CallbackFuncs.ORDER_REQUESTS_AMOUNT, args))))
        elif btn_set == cls.INL_PRICE:
            ikey.add(*(InlineKeyboardButton(sym + misc.price_buttons[x], callback_data=set_callback(CallbackFuncs.CHOOSE_PRICE, 2 ** x)) for x, sym in enumerate(args)))
            ikey.add(InlineKeyboardButton(misc.next_button, callback_data=set_callback(CallbackFuncs.CHOOSE_PRICE_SUBMIT, None)))
        elif btn_set == cls.INL_CLIENT_CATEGORIES:
            ikey.add(*(InlineKeyboardButton(f'{args[cat]}', callback_data=set_callback(CallbackFuncs.NEW_ORDER_CATEGORIES, cat)) for cat in args))
        elif btn_set == cls.INL_CLIENT_SUBCATEGORIES:
            ikey.add(*(InlineKeyboardButton(text, callback_data=set_callback(CallbackFuncs.NEW_ORDER_SUBCATEGORIES, data)) for text, data in args))
            ikey.add(InlineKeyboardButton('⬅ Назад к категориям', callback_data=set_callback(CallbackFuncs.NEW_ORDER_CHOOSE_CATEGORY)))
        elif btn_set == cls.INL_CLIENT_DATE:
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days = [now + timedelta(x) for x in range(8)]
            ikey.add(InlineKeyboardButton('На ближайшее время', callback_data=set_callback(CallbackFuncs.CHOOSE_DAY, 0)))
            ikey.add(*(InlineKeyboardButton(f'{day.day} {misc.month_names[day.month - 1]}', callback_data=set_callback(CallbackFuncs.CHOOSE_DAY, int(day.timestamp()))) for day in days))
        elif btn_set == cls.INL_CLIENT_TIME:
            ikey.row_width = 2
            ikey.add(*(InlineKeyboardButton(x, callback_data=set_callback(CallbackFuncs.CHOOSE_TIME, x)) for x in misc.times))
            ikey.add(InlineKeyboardButton(misc.next_button, callback_data=set_callback(CallbackFuncs.CHOOSE_TIME_SUBMIT, None)))
        elif btn_set == cls.INL_MASTER_CATEGORIES:
            ikey.add(*(InlineKeyboardButton(f'{args[cat][0]} ({args[cat][1]})', callback_data=set_callback(CallbackFuncs.MASTER_CATEGORIES, cat)) for cat in args))
        elif btn_set == cls.INL_MASTER_SUBCATEGORIES:
            ikey.add(*(InlineKeyboardButton(text, callback_data=set_callback(CallbackFuncs.CHOOSE_SUBCATEGORY, data)) for text, data in args))
            ikey.add(InlineKeyboardButton('⬅ Назад к категориям', callback_data=set_callback(CallbackFuncs.CHOOSE_CATEGORY)))
        elif btn_set == cls.INL_MASTER_PRICES:
            ikey.add(*(InlineKeyboardButton(f'{x[0]} грн. – {x[1]} заказов', callback_data=set_callback(CallbackFuncs.MASTER_PRICE, x[0])) for x in args))
        elif btn_set == cls.INL_ORDERS_HISTORY:
            ikey.add(*(InlineKeyboardButton(x[1], callback_data=set_callback(CallbackFuncs.ORDER_INFO, x[0])) for x in args))
        elif btn_set == cls.INL_ORDER_DELETE:
            ikey.add(InlineKeyboardButton('Удалить заказ', callback_data=set_callback(CallbackFuncs.ORDER_DELETE, args)))
        return key or ikey


class MediaGroup:
    def __init__(self, data=None, prefer_photo=True):
        """
        :param data: Dict{'text': String, 'photo': List[str], 'video': List[str]} | Portfolio ->
                     Photo and video are lists of their file_id
        :param prefer_photo: If the amount of medias is more than the limit, reduce the number of photos or videos
                             in favor of the photos, otherwise of the videos
        """
        if data is None:
            data = {}
        self.prefer_photo = prefer_photo
        self.photo_limit = 10
        self.video_limit = 10
        if isinstance(data, models.Portfolio):
            data = MediaGroup.from_model(data)
        self.text = data.get('text')
        self.photo = data.get('photo') or []
        self.video = data.get('video') or []

    def __bool__(self):
        return any((self.text, self.photo, self.video))

    def add(self, text=None, photo=None, video=None):
        if text: self.text = text
        if photo: self.photo.append(photo)
        if video: self.video.append(video)

    @classmethod
    def from_model(cls, portfolio: models.Portfolio):
        return {'text': portfolio.text, 'photo': json.loads(portfolio.photo), 'video': json.loads(portfolio.video)}

    @property
    def is_media_group(self):
        return len(self.photo) + len(self.video) > 1

    @property
    def to_dict(self):
        if self.prefer_photo:
            self.video_limit = self.photo_limit - len(self.photo)
        else:
            self.photo_limit = self.video_limit - len(self.video)
        return {'text': self.text, 'photo': self.photo[:self.photo_limit], 'video': self.video[:self.video_limit]}

    @property
    def to_json(self):
        return json.dumps(self.to_dict, separators=(',', ':'))


def send_media_group(chat_id: int, media: MediaGroup, caption=None, emoji_decode=True):
    text = caption or media.text
    if text and emoji_decode:
        text = emoji.emojize(text)
    if not media.is_media_group:
        if media.photo:
            return misc.bot.send_photo(chat_id, media.photo[0], caption=text)
        elif media.video:
            return misc.bot.send_video(chat_id, media.video[0], caption=text)
        elif text:
            return misc.bot.send_message(chat_id, text)
    else:
        medias_wrapped = []
        if media.photo:
            medias_wrapped += [InputMediaPhoto(media.photo[0], caption=text)] \
                            + [InputMediaPhoto(x) for x in media.photo[1:]]
        if media.video:
            shift = 0
            if not media.photo:
                medias_wrapped += [InputMediaVideo(media.video[0], caption=text)]
                shift = 1
            medias_wrapped += [InputMediaVideo(x) for x in media.video[shift:]]
        return misc.bot.send_media_group(chat_id, medias_wrapped)[0]


def answer(message, text, reply_markup=None, pm=True, **kwargs):
    def send_message(func, _type, *types, **kw):
        for t in types:
            if kwargs.get(t):
                del kwargs[t]
        try:
            func(message.chat.id, reply_markup=reply_markup, parse_mode='Markdown' if pm else None, **kwargs, **kw)
        except ApiTelegramException:
            del kwargs[_type]
            misc.bot.send_message(message.chat.id, text, parse_mode='Markdown' if pm else None, **kwargs, **kw)
    if text == '-':
        text = None
    if kwargs.get('photo') and kwargs['photo'] != '-':
        send_message(misc.bot.send_photo, 'photo', 'data', 'animation', caption=text)
    elif kwargs.get('data') and kwargs['data'] != '-':
        send_message(misc.bot.send_video, 'data', 'photo', 'animation', caption=text)
    elif kwargs.get('animation') and kwargs['animation'] != '-':
        send_message(misc.bot.send_animation, 'animation', 'photo', 'data', caption=text)
    else:
        send_message(misc.bot.send_message, None, 'photo', 'data', 'animation', text=text)


def user_handler(function):
    def decorator(message, **kwargs):
        user, created = models.User.objects.get_or_create(
                                   user_id=message.from_user.id,
                                   defaults={'user_id': message.from_user.id,
                                             'username': message.from_user.username,
                                             'first_name': message.from_user.first_name,
                                             'last_name': message.from_user.last_name})
        if not created:
            if user.is_banned:
                return
            user.username = message.from_user.username
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            user.save()
        kwargs['user'] = user
        kwargs['created'] = created
        if function.__name__ == 'decorator':
            expected = kwargs
        else:
            expected = {key: kwargs[key] for key in function.__code__.co_varnames if kwargs.get(key) is not None}
        return function(message, **expected)
    return decorator


def logger_middleware(type_, content=None, is_callback=False):
    def wrapper(function):
        def decorator(message, *args, **kwargs):
            user = get_instance(args, models.User)
            if not user:
                user = kwargs.get('user')
            if user:
                button = None
                if is_callback:
                    callback = get_instance(args, CallbackQuery)
                    key = callback.message.reply_markup.to_dict()['inline_keyboard']
                    button = [res[0] for res in [[button['text'] for button in row if button.get('callback_data') == callback.data] for row in key] if res][0]
                models.Log.objects.create(user=user, type=type_, content=content or button or message.text)
            if function.__name__ == 'decorator':
                expected = kwargs
            else:
                expected = {key: kwargs[key] for key in function.__code__.co_varnames if kwargs.get(key) is not None}
            return function(message, *args, **expected)
        return decorator
    return wrapper


def reset_state_checker(text, buttons):
    def wrapper(function):
        def decorator(message, *args, **kwargs):
            user = get_instance(args, models.User)
            if not user:
                user = kwargs.get('user')
            if user and message.text == misc.back_button:
                user.reset_state()
                answer(message, user.text(text), reply_markup=ButtonSet(buttons))
                return
            return function(message, *args, **kwargs)
        return decorator
    return wrapper


def get_instance(__objects, __class_or_tuple):
    for __obj in __objects:
        if isinstance(__obj, __class_or_tuple):
            return __obj


def exec_protected(func, *args, **kwargs):
    # noinspection PyBroadException
    try:
        return func(*args, **kwargs)
    except Exception:
        for admin in settings.DEVS:
            with suppress(Exception):
                misc.bot.send_message(admin, traceback.format_exc())


def set_callback(func, data=None):
    return callback_data.CallbackData('@', 'func', 'json', sep='&').new(func, json.dumps(data, separators=(',', ':')))


def get_callback(data):
    try:
        cd = callback_data.CallbackData('@', 'func', 'json', sep='&').parse(data)
    except ValueError:
        return
    parsed = cd.get('json')
    func = cd.get('func')
    if parsed is None or func is None or not func.isdigit():
        return
    return int(func), json.loads(parsed)


def broadcast_to_admins(text, func=misc.bot.send_message, **kwargs):
    for admin in preferences.Settings.admins.split():
        with suppress(ApiTelegramException):
            func(admin, text, **kwargs)


def distinct(obj, key):
    result = []
    uniq = []
    for item in obj:
        attr = item.__getattribute__(key)
        if attr not in uniq:
            result.append(item)
            uniq.append(attr)
    return result


def esc_md(s):
    if s is None:
        return ''
    if isinstance(s, str):
        if not s: return ''
        return s.replace('_', '\\_').replace('*', '\\*').replace('`', "'").replace('[', '\\[')
    if isinstance(s, dict):
        return {key: esc_md(x) for key, x in s.items()}
    if isinstance(s, list):
        return list(map(lambda x: esc_md(x), s))
    if isinstance(s, (int, float, bool)):
        return str(s)


def get_location(latitude: float, longitude: float, lang='en', pretty=0, no_annotations=1):
    response = requests.get(misc.opencage_api_url, params={
        'key': OPENCAGE_KEY,
        'q': f'{latitude},{longitude}',
        'language': lang,
        'pretty': pretty,
        'no_annotations': no_annotations,
        'roadinfo': 1
    })
    if response.status_code == 200:
        result = response.json()
        return result['results'][0]['components']


def get_city(latitude: float, longitude: float, lang='en'):
    location = get_location(latitude, longitude, lang)
    if not location:
        return
    country, _ = models.Country.objects.get_or_create(name=location.get('country'),
                                                      defaults={'name': location.get('country')})
    city_name = location.get('state') or location.get('city')
    city, _ = models.City.objects.get_or_create(name=city_name, country=country,
                                                defaults={'name': city_name, 'country': country})
    return city


def get_address(latitude: float, longitude: float, lang='ru'):
    location = get_location(latitude, longitude, lang)
    if not location:
        return
    ret = list()
    ret.append(location.get('state'))
    if location.get('city'):
        ret.append(location.get('city'))
    else:
        ret.append(location.get('county'))
        ret.append(location.get('hamlet'))
    ret.append(location.get('road'))

    ret = filter(lambda x: x is not None, ret)
    ret = ', '.join(ret)
    if ret:
        return ret


def media_group_collector(data: dict):
    media = MediaGroup(data)
    if data.get('media_group_id'):
        for obj in models.MediaGroupHelper.objects.filter(media_group_id=data['media_group_id']):
            media.add(photo=obj.photo_id, video=obj.video_id)
    return media


def media_extractor(message, user: models.User):
    if message.media_group_id:
        user.update_state_data({'media_group_id': message.media_group_id})
    media = MediaGroup(user.get_state_data())
    if message.photo:
        if message.media_group_id:
            models.MediaGroupHelper.objects.create(media_group_id=message.media_group_id,
                                                   photo_id=message.photo[-1].file_id)
        else:
            media.add(photo=message.photo[-1].file_id)
            user.update_state_data(media.to_dict)
    elif message.video:
        if message.media_group_id:
            models.MediaGroupHelper.objects.create(media_group_id=message.media_group_id,
                                                   video_id=message.video.file_id)
        else:
            media.add(video=message.video.file_id)
            user.update_state_data(media.to_dict)
    else:
        if message.document:
            answer(message, user.text('media_error_file'), reply_to_message_id=message.message_id,
                   allow_sending_without_reply=True)
        else:
            answer(message, user.text('media_error_else'), reply_to_message_id=message.message_id,
                   allow_sending_without_reply=True)


def bulk_mailing(order, data):
    latitude_dist = 111.3
    longitude_dist = cos(radians(order.location.x)) * latitude_dist
    a = order.location.x + (order.subcategory.category.radius / latitude_dist)
    d = order.location.x - (order.subcategory.category.radius / latitude_dist)
    b = order.location.y - (order.subcategory.category.radius / longitude_dist)
    c = order.location.y + (order.subcategory.category.radius / longitude_dist)
    masters = models.User.objects.\
        annotate(location_x=ExpressionWrapper(Func('location', function='ST_X'), output_field=FloatField()),
                 location_y=ExpressionWrapper(Func('location', function='ST_Y'), output_field=FloatField())).\
        filter(type=User.MASTER, categories=order.subcategory, is_active=True,
               location_x__lte=a, location_x__gte=d, location_y__lte=c, location_y__gte=b)
    price = ''
    for i in range(3):
        if data['price'] & 2 ** i:
            if price:
                price += ', '
            price += misc.price_buttons[i]
    form_text = esc_md(data.get('text') or '-')
    times = ', '.join(json.loads(order.times))
    text = f"*Новый заказ!*\n*Категория:* {order.subcategory.category.title} – {order.subcategory.title}\n" \
           f"*Дата*: {order.date.day} {misc.month_names[order.date.month - 1]}\n" \
           f"*Время:* {times}\n*Ценовая категория:* {price}\n*Комментарий:* {form_text}"
    media = media_group_collector(data)
    media.text = None
    media_post = send_media_group(preferences.Settings.media_chat_id, media)
    if media_post:
        text = f'[­]({preferences.Settings.media_chat_link}/{media_post.message_id})' + text
    for master in masters:
        with suppress(Exception):
            misc.bot.send_message(master.user_id, text, parse_mode='Markdown', reply_markup=ButtonSet(ButtonSet.INL_MASTER_ACCEPT_ORDER, order.id))
            sleep(.05)


def way_for_pay_request_purchase(user_id, amount):
    date = int(time())
    order_reference = f'{date}_{user_id}'
    secret = settings.WAY_FOR_PAY_SECRET.encode('utf-8')
    str_signature = f'{settings.WAY_FOR_PAY_MERCHANT_ID};{misc.way_for_pay_merchant_domain_name};{order_reference};{date};{amount};UAH;Пополнение баланса;1;{amount}'.encode('utf-8')
    hash_signature = hmac.new(secret, str_signature, 'MD5').hexdigest()
    res = requests.post(misc.way_for_pay_url, json={
        'transactionType': 'CREATE_INVOICE',
        'merchantAccount': settings.WAY_FOR_PAY_MERCHANT_ID,
        'merchantAuthType': 'SimpleSignature',
        'apiVersion': 1,
        'merchantDomainName': misc.way_for_pay_merchant_domain_name,
        'merchantTransactionSecureType': 'AUTO',
        'merchantSignature': hash_signature,
        'serviceUrl': settings.WAY_FOR_PAY_SERVICE_URL,
        'orderReference': order_reference,
        'orderDate': date,
        'amount': amount,
        'currency': 'UAH',
        'productName': ['Пополнение баланса'],
        'productPrice': [amount],
        'productCount': [1],
    })
    response = json.loads(res.text)
    if response['reason'] == 'Ok':
        return response['invoiceUrl']
    else:
        return False, response['reason']
