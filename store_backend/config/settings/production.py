# -*- coding: utf-8 -*-
"""
Production Configurations

"""

from .common import *  # noqa
from environs import Env, EnvValidationError

# Normally you should not import ANYTHING from Django directly
# into your settings, but ImproperlyConfigured is an exception.
from django.core.exceptions import ImproperlyConfigured


# Environment variables-based secrets
env = Env()
env.read_env()  # also read .env file, if it exists


def get_secret(setting, secret_type=env):
    """Get the secret variable or return explicit exception."""
    try:
        return secret_type(setting)
    except EnvValidationError as e:
        raise ImproperlyConfigured(str(e))


# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/4.2/ref/settings/#secret-key
SECRET_KEY = get_secret('DJANGO_SECRET_KEY')


# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/4.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = get_secret('DJANGO_ALLOWED_HOSTS', env.list)
# END SITE CONFIGURATION


# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
DATABASES['default']['NAME'] = get_secret('POSTGRES_DB')
DATABASES['default']['USER'] = get_secret('POSTGRES_USER')
DATABASES['default']['PASSWORD'] = get_secret('POSTGRES_PASSWORD')
DATABASES['default']['HOST'] = get_secret('DATABASE_HOST')
DATABASES['default']['PORT'] = get_secret('DATABASE_PORT')


# LOGGING CONFIGURATION
# See https://docs.djangoproject.com/en/4.2/topics/logging/ for
# more details on how to customize your logging configuration.
ADMINS = [('FNNDSC Developers', 'dev@babymri.org')]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '[%(levelname)s][%(module)s %(process)d %(thread)d] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        '': {  # root logger
            'level': 'INFO',
            'handlers': ['console'],
        }
    }
}


# CORSHEADERS
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = get_secret('DJANGO_CORS_ALLOW_ALL_ORIGINS', env.bool)
CORS_ALLOWED_ORIGINS = get_secret('DJANGO_CORS_ALLOWED_ORIGINS', env.list)

# REVERSE PROXY
# ------------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = get_secret('DJANGO_SECURE_PROXY_SSL_HEADER', env.list)
SECURE_PROXY_SSL_HEADER = tuple(SECURE_PROXY_SSL_HEADER) if SECURE_PROXY_SSL_HEADER else None
USE_X_FORWARDED_HOST = get_secret('DJANGO_USE_X_FORWARDED_HOST', env.bool)
