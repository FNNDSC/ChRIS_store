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
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = get_secret('DJANGO_SECRET_KEY')


# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = get_secret('DJANGO_ALLOWED_HOSTS', env.list)
# END SITE CONFIGURATION


# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
DATABASES['default']['NAME'] = get_secret('MYSQL_DATABASE')
DATABASES['default']['USER'] = get_secret('MYSQL_USER')
DATABASES['default']['PASSWORD'] = get_secret('MYSQL_PASSWORD')
DATABASES['default']['HOST'] = get_secret('DATABASE_HOST')
DATABASES['default']['PORT'] = get_secret('DATABASE_PORT')


# SWIFT SERVICE CONFIGURATION
# ------------------------------------------------------------------------------
DEFAULT_FILE_STORAGE = 'swift.storage.SwiftStorage'
SWIFT_AUTH_URL = get_secret('SWIFT_AUTH_URL')
SWIFT_USERNAME = get_secret('SWIFT_USERNAME')
SWIFT_KEY = get_secret('SWIFT_KEY')
SWIFT_CONTAINER_NAME = get_secret('SWIFT_CONTAINER_NAME')
SWIFT_AUTO_CREATE_CONTAINER = True


# LOGGING CONFIGURATION
# See http://docs.djangoproject.com/en/2.2/topics/logging for
# more details on how to customize your logging configuration.
ADMINS = [('FNNDSC Developers', 'dev@babymri.org')]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '[%(levelname)s][%(name)s][%(filename)s:%(lineno)d %(funcName)s] %(message)s'
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


# Your production stuff: Below this line define 3rd party library settings

# CORSHEADERS
# ------------------------------------------------------------------------------
CORS_ORIGIN_ALLOW_ALL = get_secret('DJANGO_CORS_ORIGIN_ALLOW_ALL', env.bool)
CORS_ORIGIN_WHITELIST = get_secret('DJANGO_CORS_ORIGIN_WHITELIST', env.list)
