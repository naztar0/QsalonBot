import json
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from preferences.models import Preferences
from bot import types
from bot.misc import i18n, __


class User(models.Model):
    TYPES = ((types.User.CLIENT, 'Клиент'), (types.User.MASTER, 'Мастер'))
    created = models.DateTimeField('🕐 Создан, по UTC', auto_now_add=True)
    user_id = models.BigIntegerField('ID', unique=True, primary_key=True)
    username = models.CharField('@юзернейм', max_length=256, blank=True, null=True)
    first_name = models.CharField('Имя', max_length=256, blank=True, null=True)
    last_name = models.CharField('Фамилия', max_length=256, blank=True, null=True)
    type = models.CharField('Тип', max_length=8, default=None, null=True, choices=TYPES)
    categories = models.ManyToManyField('Subcategory', verbose_name='Суб-категории', default=None)
    portfolio = models.ForeignKey('Portfolio', models.CASCADE, verbose_name='Портфолио', default=None, null=True)
    location = models.PointField('Локация', geography=True, default=Point(0, 0))
    city = models.ForeignKey('City', models.CASCADE, verbose_name='Город', default=None, null=True)
    balance = models.PositiveIntegerField('Баланс', default=0)
    is_active = models.BooleanField('Активен', default=False)
    is_banned = models.BooleanField('Бан', default=False)
    language = i18n.default
    # service only
    state = models.CharField(max_length=256, default=None, null=True)
    state_data = models.TextField(max_length=16384, default=None, null=True)

    def text(self, name):
        return __(name, locale=self.language)

    def set_state(self, state):
        self.state = state
        self.save()

    def reset_state(self):
        self.state = None
        self.state_data = None
        self.save()

    def get_state_data(self) -> dict:
        return json.loads(self.state_data or '{}')

    def update_state_data(self, data: dict) -> dict:
        temp = json.loads(self.state_data or '{}')
        temp.update(data)
        self.state_data = json.dumps(temp)
        self.save()
        return temp

    def __str__(self):
        return str(self.user_id)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class Log(models.Model):
    TYPES = ((types.Log.TEXT, '🅰️ Текст'), (types.Log.REPLY_BUTTON, '⏹ Reply-кнопка'),
             (types.Log.INLINE_BUTTON, '⏺ Inline-кнопка'), (types.Log.COMMAND, '✳️ Команда'))
    created = models.DateTimeField('🕐 Создан, по UTC', auto_now_add=True)
    user = models.ForeignKey(User, models.CASCADE)
    type = models.CharField('Тип', max_length=16, choices=TYPES)
    content = models.CharField('Контент', max_length=4096, blank=True, null=True)

    def __str__(self):
        return str(self.content)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'лог'
        verbose_name_plural = 'логи'


class Country(models.Model):
    name = models.CharField('Страна', max_length=128)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField('Город', max_length=128)
    country = models.ForeignKey(Country, models.CASCADE, verbose_name='Страна')

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    text = models.CharField('Текст', max_length=4096, default=None, null=True)
    photo = models.CharField('Фото', max_length=2048, default=None, null=True)
    video = models.CharField('Видео', max_length=2048, default=None, null=True)
    message_id = models.PositiveIntegerField(default=None, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'портфолио'
        verbose_name_plural = 'портфолио'


class Category(models.Model):
    title = models.CharField('Название', max_length=512)
    radius = models.PositiveIntegerField('Радиус, км', default=5)

    @property
    def subcategories(self):
        return Subcategory.objects.filter(category=self)

    def __str__(self):
        return str(self.title)

    class Meta:
        ordering = ('id',)
        verbose_name = 'категория'
        verbose_name_plural = 'категории'


class Subcategory(models.Model):
    title = models.CharField('Название', max_length=512)
    category = models.ForeignKey(Category, models.CASCADE, verbose_name='Категория')

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'суб-категория'
        verbose_name_plural = 'суб-категории'


class Order(models.Model):
    created = models.DateTimeField('🕐 Создан, по UTC', auto_now_add=True)
    client = models.ForeignKey(User, models.CASCADE, verbose_name='Клиент', related_name='client')
    master = models.ForeignKey(User, models.CASCADE, verbose_name='Мастер', related_name='master', default=None, null=True)
    subcategory = models.ForeignKey(Subcategory, models.CASCADE, verbose_name='Суб-категория')
    location = models.PointField('Локация', geography=True)
    city = models.ForeignKey(City, models.CASCADE, verbose_name='Город', default=None, null=True)
    date = models.DateField('Дата')
    times = models.CharField('Время', max_length=512)
    message_id = models.PositiveIntegerField(default=None, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


class Request(models.Model):
    created = models.DateTimeField('🕐 Создан, по UTC', auto_now_add=True)
    order = models.ForeignKey(Order, models.CASCADE, verbose_name='Заказ')
    master = models.ForeignKey(User, models.CASCADE, verbose_name='Мастер')
    message_id = models.PositiveIntegerField(default=None, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'отклик'
        verbose_name_plural = 'отклики'


class Transaction(models.Model):
    created = models.DateTimeField('🕐 Создан, по UTC', auto_now_add=True)
    user = models.ForeignKey(User, models.CASCADE, verbose_name='Мастер')
    amount = models.PositiveIntegerField('Сумма')
    currency = models.CharField('Валюта', max_length=16)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'транзакция'
        verbose_name_plural = 'транзакции'


class Price(models.Model):
    amount = models.PositiveIntegerField('Количество кликов')
    price = models.PositiveIntegerField('Стоимость')

    def __str__(self):
        return str(self.price)

    class Meta:
        verbose_name = 'цена'
        verbose_name_plural = 'цены'


class Settings(Preferences):
    media_chat_link = models.URLField('Ссылка на чат медиа', max_length=64, default='-')
    portfolio_chat_link = models.URLField('Ссылка на чат портфолио', max_length=64, default='-')
    media_chat_id = models.BigIntegerField('ID чата медиа', default=0)
    portfolio_chat_id = models.BigIntegerField('ID чата портфолио', default=0)

    def __str__(self):
        return 'Настройки'

    class Meta:
        verbose_name = 'список'
        verbose_name_plural = 'списки'


class Post(models.Model):
    STATUSES = ((types.Post.WAIT, '⏳ Ожидание'), (types.Post.SEND, '📨 Отправка'), (types.Post.DONE, '🎫 Готово'))
    USER_TYPES = ((types.User.CLIENT, 'Клиент'), (types.User.MASTER, 'Мастер'))
    created = models.DateTimeField('🕐 Создано', auto_now_add=True)
    status = models.CharField('Статус', max_length=4, choices=STATUSES, default=types.Post.WAIT)
    photo_id = models.CharField('Фото', max_length=128, blank=True, null=True)
    photo_id.help_text = "Указывается по FileID, его можно получить отправив боту нужное вам фото."
    gif_id = models.CharField('GIF', max_length=128, blank=True, null=True)
    gif_id.help_text = "Указывается по FileID, его можно получить отправив боту нужное вам gif."
    video_id = models.CharField('Видео', max_length=128, blank=True, null=True)
    video_id.help_text = "Указывается по FileID, его можно получить отправив боту нужное вам видео."
    message = models.TextField("Сообщение", max_length=1024)
    preview = models.BooleanField("Превью", default=True)
    button = models.CharField("Кнопка", max_length=256, blank=True, null=True)
    link = models.URLField("Ссылка", blank=True, null=True)
    receivers = models.IntegerField("Получатели", blank=True, null=True)
    user_type = models.CharField(max_length=8, choices=USER_TYPES, verbose_name='Тип', blank=True, default=None, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class MediaGroupHelper(models.Model):
    media_group_id = models.PositiveBigIntegerField()
    photo_id = models.CharField(max_length=128, default=None, null=True)
    video_id = models.CharField(max_length=128, default=None, null=True)


class Stats:
    class Meta:
        proxy = True
        verbose_name = 'статистика'
        verbose_name_plural = 'статистика'


class UserStats(User, Stats): pass
class CategoryStats(Category, Stats): pass
class OrderStats(Order, Stats): pass
class RequestStats(Request, Stats): pass
