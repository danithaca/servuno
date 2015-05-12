"""
Settings file for the s2c2 webapp.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import logging

from django.core.urlresolvers import reverse_lazy
import sys


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# content in this directory is not tracked in git.
BASE_DIR_ASSETS = os.path.join(BASE_DIR, 'assets')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'nqzos2!&+rri)*rnyodt32uba#alt!!$)0l5x$%-siw6%brub2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # should not use in production
    # 'django_extensions',

    'django.contrib.sites',

    'localflavor',
    'pytz',
    # 'pinax_theme_bootstrap',
    'bootstrapform', # from django-bootstrap-form
    # 'account',
    'easy_thumbnails',
    'image_cropping',
    'django_ajax',
    'datetimewidget',
    'rest_framework',
    'autocomplete_light',

    # customized
    's2c2',
    'location',
    'user',
    'slot',
    'log',
    'cal',
    'p2',
)

MIDDLEWARE_CLASSES = (
    # no need for this anymore because we disabled mod_expires on apache.
    # 's2c2.middleware.DisableBrowserCacheMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # external
    # 'account.middleware.LocaleMiddleware',
    # 'account.middleware.TimezoneMiddleware',
)

ROOT_URLCONF = 's2c2.urls'

WSGI_APPLICATION = 's2c2.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

# this only applies to rendering whit USE_TZ is True.
TIME_ZONE = 'America/Detroit'
# TIME_ZONE = 'UTC'

USE_I18N = False    # True

USE_L10N = False    # True

# This makes django save datetime in UTC.
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR_ASSETS, 'static')

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",

    # add 'request' in context, which can be accessed from within template.
    'django.core.context_processors.request',
    # 'pinax_theme_bootstrap.context_processors.theme',
    # 'account.context_processors.account',

    # add 'user_profile' to request
    'user.context_processors.current_user_profile',

    # add notification count
    'log.context_processors.notification_count',
)

# not added from startproject. need to manually add this.
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# production site should use another folder not in git.
MEDIA_ROOT = os.path.join(BASE_DIR_ASSETS, 'media')
MEDIA_URL = '/media/'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = reverse_lazy('user:login')
LOGOUT_URL = reverse_lazy('user:logout')

TIME_FORMAT = 'h:iA'

ADMINS = (('admin', 'danithaca@gmail.com'), )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
        'simple': {
            'format': '%(levelname)s %(message)s'
            },
        },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            },
        },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        },
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'ERROR',
            },
        's2c2.management': {
            'handlers': ['console'],
            'level': 'DEBUG',
            },
    }

# for thumbnail processing.
from easy_thumbnails.conf import Settings as thumbnail_settings
THUMBNAIL_PROCESSORS = ('image_cropping.thumbnail_processors.crop_corners',) + thumbnail_settings.THUMBNAIL_PROCESSORS

# IMAGE_CROPPING_JQUERY_URL = 'https://code.jquery.com/jquery-2.1.3.min.js'
IMAGE_CROPPING_THUMB_SIZE = (400, 400)
IMAGE_CROPPING_SIZE_WARNING = True

# remove green (clashes with other calendar colors), gray, black
COLORS = ['maroon',
          'navy',
          'red',
          'teal',
          'blue',
          'orange',
          'yellowgreen',
          'aqua',
          'purple',
          'fuchsia',
          'lime',
          'olive']

CALENDAR_EVENT_COLOR_EMPTY = 'gray'
CALENDAR_EVENT_COLOR_FILLED = 'darkgreen'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ]
}

SITE_ID = 1

# load local settings override.

try:
    from s2c2.settings_local import *
except ImportError:
    logging.warning('Local settings not found.')
