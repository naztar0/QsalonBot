from typing import Any, Callable, List, Optional, Union
from django.db import models
from telebot import types, REPLY_MARKUP_TYPES
from bot.utils_lib import helper
from bot.misc import bot


class Log(helper.HelperMode):
    mode = helper.HelperMode.SCREAMING_SNAKE_CASE
    TEXT = helper.Item()
    REPLY_BUTTON = helper.Item()
    INLINE_BUTTON = helper.Item()
    COMMAND = helper.Item()


class User(helper.HelperMode):
    mode = helper.HelperMode.SCREAMING_SNAKE_CASE
    CLIENT = helper.Item()
    MASTER = helper.Item()


class Post(helper.HelperMode):
    mode = helper.HelperMode.SCREAMING_SNAKE_CASE
    WAIT = helper.Item()
    SEND = helper.Item()
    DONE = helper.Item()


class MessageField(models.TextField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 4096
        kwargs['default'] = '-'
        super().__init__(*args, **kwargs)


class ButtonField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 64
        kwargs['default'] = '-'
        super().__init__(*args, **kwargs)


class MediaField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 128
        kwargs['default'] = '-'
        super().__init__(*args, **kwargs)


class AlertField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 200
        kwargs['default'] = '-'
        super().__init__(*args, **kwargs)
