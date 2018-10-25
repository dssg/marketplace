"""Django settings for DSSG Marketplace project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/

"""
import os

import requests
from decouple import Csv, config
from dj_database_url import parse as db_url
from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_ID = 1

SITE_NAME = config('SITE_NAME', default='DSSG Solve')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

if DEBUG:
    EC2_PRIVATE_IP = None
else:
    # TODO: Could perhaps instead determine this value at EC2 instance
    # TODO: initialization (via user data or something)?
    # TODO: ...Such that container processes can retrieve it locally
    # TODO: (or from the host)?
    try:
        response = requests.get(
            'http://169.254.169.254/latest/meta-data/local-ipv4',
            timeout=0.01
        )
    except requests.exceptions.RequestException:
        EC2_PRIVATE_IP = None
    else:
        EC2_PRIVATE_IP = response.text

    if EC2_PRIVATE_IP:
        ALLOWED_HOSTS.append(EC2_PRIVATE_IP)

file_storage_option = config('DEFAULT_FILE_STORAGE', default='') or 'filesystem'
file_storage_options = {'s3', 'whitenoise', 'filesystem'}
if file_storage_option not in file_storage_options:
    raise ImproperlyConfigured("unrecognized value for DEFAULT_FILE_STORAGE: "
                               f"{file_storage_option!r} not in {file_storage_options}")


# Application definition

INSTALLED_APPS = [
    # our apps
    'marketplace.apps.MarketplaceConfig',

    # social login
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # ...enabled providers
	# 'allauth.socialaccount.providers.bitbucket',
    # 'allauth.socialaccount.providers.bitbucket_oauth2',
    # 'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    # 'allauth.socialaccount.providers.gitlab',
    'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.linkedin',
    # 'allauth.socialaccount.providers.linkedin_oauth2',

    # third-party apps
    'django_countries',
    'rules',
    'markdown_deux',
    'widget_tweaks',

    # django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
]

if file_storage_option == 's3':
    INSTALLED_APPS.append('storages')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'marketplace.middleware.UserTypeMiddleware',
]

if file_storage_option == 'whitenoise':
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')


ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'marketplace.context_processors.ga_tracking_id',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': config(
        'DATABASE_URL',
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'),
        cast=db_url,
    )
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = (
    'rules.permissions.ObjectPermissionBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'marketplace.User'

LOGIN_REDIRECT_URL = 'marketplace:home'

LOGIN_URL = 'marketplace:login'

# allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # unnecessary for installed providers?
SOCIALACCOUNT_ADAPTER = 'marketplace.socialauth.adapter.SocialAccountAdapter'

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = config('TIME_ZONE')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

## Not using S3 will make the static and user uploaded files to only work when
## DEBUG = True. When not in debug mode, Django will not serve those files locally
## so it needs a remote storage system.
## Whitenoise works for serving static files locally, but not for user-uploaded files.
if file_storage_option == 's3':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_QUERYSTRING_AUTH = False
    AWS_LOCATION = 'static'

    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default=None)

    if config('AWS_S3_ENDPOINT_URL', default=None):
        AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')

    if DEBUG:
        AWS_AUTO_CREATE_BUCKET = True


STATIC_URL = '/static/'
if DEBUG:
    STATIC_ROOT = '/tmp/dssgsolve/static/'
else:
    STATIC_ROOT = '/app/static/'

MEDIA_ROOT = os.path.join(STATIC_ROOT, 'uploads/')
MEDIA_URL = "/media/"

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = '/tmp/app-messages'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')


if DEBUG:
    LOGS_HOME = '.'
else:
    LOGS_HOME = '/var/log/webapp'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_HOME,'dssgsolve.log'),
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level': config('DJANGO_LOG_LEVEL', default='WARN'),
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': config('DJANGO_DB_LOG_LEVEL', default='WARN'),
            'propagate': False,
        },
        'marketplace': {
            'handlers': ['console', 'logfile'],
            'level': config('DSSG_LOG_LEVEL', default='WARN'),
        },
    }
}



MESSAGE_TAGS = {
    messages.DEBUG: 'bg-light',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}


RECAPTCHA_SITE_KEY = config('RECAPTCHA_SITE_KEY', default=None)
RECAPTCHA_SECRET_KEY = config('RECAPTCHA_SECRET_KEY', default=None)

AUTOMATICALLY_ACCEPT_VOLUNTEERS = config('AUTOMATICALLY_ACCEPT_VOLUNTEERS', default=False, cast=bool)

GA_TRACKING_ID = config('GA_TRACKING_ID', default=None)
