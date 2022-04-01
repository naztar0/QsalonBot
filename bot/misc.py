import logging
from django.conf import settings
from pathlib import Path
from telebot import TeleBot
from bot.utils_lib.i18n import I18nMiddleware


app_dir: Path = Path(__file__).parent.parent
locales_dir = app_dir / "locales"
temp_dir = app_dir / "temp"

logging.basicConfig(level=logging.DEBUG)
i18n = I18nMiddleware('bot', locales_dir, default='ru')

bot = TeleBot(settings.TG_TOKEN, threaded=False)
__ = i18n.gettext

opencage_api_url = "https://api.opencagedata.com/geocode/v1/json"
way_for_pay_url = "https://api.wayforpay.com/api"
way_for_pay_merchant_domain_name = "www.t.me/AdvancedAdsBot"

role_buttons = ("Клиент", "Мастер")
client_buttons = ("Заказать услугу", "Мои услуги")
master_buttons_1 = ("Принятые заказы", "Мой профиль", "Пополнить баланс")
master_buttons_2 = ("Подписки", "Портфолио", "Местоположение", "⬅ Назад­")
back_button = "⬅ Назад"
next_button = "Далее ➡"
save_changes = "✅ Закончить выбор"
top_up_balance = "Пополнить баланс"
create_button = "Создать"
edit_buttons = ("Изменить всё", "Изменить описание", "Изменить медиа")
price_buttons = ("до 400 грн.", "400-700 грн.", "от 700 грн.")

month_names = ("января", "февраля", "марта", "апреля", "мая", "июня",
               "июля", "августа", "сентября", "октября", "ноября", "декабря")
times = ('8:00', '8:30', '9:00', '9:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
         '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
         '20:00', '20:30', '21:00')

hint_video_id = ''
