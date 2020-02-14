import os

from django.utils.translation import gettext_lazy as _

from . import get_env, default_internal_ips, default_wsgi

env = get_env()

SITE_TITLE = _('VPRAD SITE')
INTERNAL_IPS = default_internal_ips()
PROJECT_ROOT = env('PROJECT_ROOT',
                   default=os.getcwd())
DEBUG = env.bool('DJANGO_DEBUG',
                 default=False)
ENVIRONMENT = env('DJANGO_ENVIRONMENT',
                  default="production")
SECRET_KEY = env('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS',
                         default=['localhost', '127.0.0.1'])
THIRD_PARTY_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'django_tables2',
    'django_filters',
]
VRAD_APPS = [
    'vprad.actions',
    'vprad.views',
    'vprad.site',
    'vprad'
]
INSTALLED_APPS = THIRD_PARTY_APPS + VRAD_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'vprad.auth.AuthMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(-1, 'debug_toolbar.middleware.DebugToolbarMiddleware')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'vprad.site.jinja.environment'
        }
    },
    {   # Needed for django_tables2 templates.
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
    },
]

ROOT_URLCONF = 'vprad.site.urls'

WSGI_APPLICATION = default_wsgi()

DATABASES = {
    'default': env.db('DATABASE_URL'),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True
DJANGO_TABLES2_TEMPLATE = 'django_tables2/semantic.html'
STATIC_URL = '/static/'


# region Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)-8s %(name)-10s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
    }
}
# endregion


def set_logger(logger: str, level: str = None, handlers=None, propagate=None):
    if logger not in LOGGING['loggers']:
        LOGGING['loggers'][logger] = {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        }
    if level:
        LOGGING['loggers'][logger]['level'] = level
    if handlers:
        LOGGING['loggers'][logger]['handlers'] = handlers
    if not propagate is None:
        LOGGING['loggers'][logger]['propagate'] = propagate


set_logger('django', level='ERROR')
set_logger('vprad', level='WARNING')
