import os
from envparse import env
from dotenv import load_dotenv

if os.name == 'nt':
    VENV_BASE = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo\\data\\proj') + ';' + os.environ['PATH']


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

SECRET_KEY = env.str('SECRET_KEY')
DEBUG = True

TG_TOKEN = env.str('TG_TOKEN')
WEBAPP_HOST = env.str('WEBAPP_HOST', default='0.0.0.0')
WEBAPP_PORT = env.int('WEBAPP_PORT', default=8080)

WEBHOOK_DOMAIN = env.str('WEBHOOK_DOMAIN', default='example.com')
WEBHOOK_BASE_PATH = env.str('WEBHOOK_BASE_PATH', default="webhook")
WEBHOOK_PATH = f'{WEBHOOK_BASE_PATH}/{SECRET_KEY}'
WEBHOOK_URL = f'https://{WEBHOOK_DOMAIN}/{WEBHOOK_PATH}'
BASE_ADMIN_PATH = f'https://{WEBHOOK_DOMAIN}'
PAYMENT_PATH = 'payment'
PORTFOLIO_PATH = 'portfolio'

MYSQL_HOST = env.str('MYSQL_HOST', default='localhost') if DEBUG else '127.0.0.1'
MYSQL_PORT = env.int('MYSQL_PORT', default=3306)
MYSQL_PASSWORD = env.str('MYSQL_PASSWORD', default='')
MYSQL_USER = env.str('MYSQL_USER', default='')
MYSQL_DB = env.str('MYSQL_DB', default='')

BOT_ADMINS = env.list('BOT_ADMINS', default=0)
OPENCAGE_KEY = env.str('OPENCAGE_KEY', default='')
WAY_FOR_PAY_SERVICE_URL = env.str('WAY_FOR_PAY_SERVICE_URL', default='')
WAY_FOR_PAY_MERCHANT_ID = env.str('WAY_FOR_PAY_MERCHANT_ID', default='')
WAY_FOR_PAY_SECRET = env.str('WAY_FOR_PAY_SECRET', default='')
GMAPS_API_KEY = env.str('GMAPS_API_KEY', default='')

ALLOWED_HOSTS = [WEBHOOK_DOMAIN, '127.0.0.1', 'localhost', '195.14.122.81']
CSRF_TRUSTED_ORIGINS = [f'https://{WEBHOOK_DOMAIN}']
DEVS = [BOT_ADMINS[0]]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    'admin_reorder',
    'preferences',

    'bot',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'admin_reorder.middleware.ModelAdminReorder',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.mysql',
        'NAME': MYSQL_DB,
        'USER': MYSQL_USER,
        'PASSWORD': MYSQL_PASSWORD,
        'HOST': MYSQL_HOST,
        'PORT': MYSQL_PORT,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


ADMIN_REORDER = [
    {
        'app': 'bot',
        'label': 'Статистика',
        'models': [
            {
                'label': '📊 Пользователи',
                'model': 'bot.UserStats'
            },
            {
                'label': '📊 Категории',
                'model': 'bot.CategoryStats'
            },
            {
                'label': '📊 Заказы',
                'model': 'bot.OrderStats'
            },
            {
                'label': '📊 Отклики',
                'model': 'bot.RequestStats'
            },
        ]
    },
    {
        'app': 'bot',
        'label': 'Информация',
        'models': [
            {
                'label': '👳🏻‍♀ Пользователи',
                'model': 'bot.User'
            },
            {
                'label': '📜 Логи',
                'model': 'bot.Log'
            },
            {
                'label': '💼 Заказы',
                'model': 'bot.Order'
            },
            {
                'label': '📩 Отклики',
                'model': 'bot.Request'
            },
            {
                'label': '💵 Транзакции',
                'model': 'bot.Transaction'
            },
            {
                'label': '👤 Портфолио',
                'model': 'bot.Portfolio'
            },
        ]
    },
    {
        'app': 'bot',
        'label': 'Наполнение',
        'models': [
            {
                'label': '📂 Категории',
                'model': 'bot.Category'
            },
            {
                'label': '📊 Суб-категории',
                'model': 'bot.Subcategory'
            },
            {
                'label': '💵 Цены',
                'model': 'bot.Price'
            },
            {
                'label': '⚙️ Настройки',
                'model': 'bot.Settings'
            },
        ]
    },
    {
        'app': 'bot',
        'label': 'Рассылка',
        'models': [
            {
                'label': '📬 Посты',
                'model': 'bot.Post'
            },
        ]
    },
]
