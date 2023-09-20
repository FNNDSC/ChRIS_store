# -*- coding: utf-8 -*-
"""
Local settings

- Run in Debug mode
- Use console backend for emails
- Add Django Debug Toolbar
- Add django-extensions as app
"""

from .common import *  # noqa

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tvtw1#&s4i9pxosr^2rnwdh0o1-ka-l+u6(@t+c)#864((*3$4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# See https://docs.djangoproject.com/en/4.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# LOGGING CONFIGURATION
# See https://docs.djangoproject.com/en/4.2/topics/logging/ for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] [%(levelname)s]'
                      '[%(name)s][%(filename)s:%(lineno)d %(funcName)s] %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s]'
                      '[%(module)s %(process)d %(thread)d] %(message)s'
        },
    },
    'handlers': {
        'console_verbose': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_simple': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'loggers': {
        '': {  # root logger
            'level': 'INFO',
            'handlers': ['console_simple'],
        },
    }
}

for app in ['collectionjson', 'plugins', 'pipelines', 'users']:
    LOGGING['loggers'][app] = {
            'level': 'DEBUG',
            'handlers': ['console_verbose'],
            'propagate': False  # required to avoid double logging with root logger
        }


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES['default']['NAME'] = 'chris_store_dev'
DATABASES['default']['USER'] = 'chris'
DATABASES['default']['PASSWORD'] = 'Chris1234'
DATABASES['default']['TEST'] = {'NAME': 'test_chris_store_dev'}
DATABASES['default']['HOST'] = 'chris_store_dev_db'
DATABASES['default']['PORT'] = '5432'

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# django-debug-toolbar
# ------------------------------------------------------------------------------
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INSTALLED_APPS += ['debug_toolbar']

INTERNAL_IPS = ['127.0.0.1', ]

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ['django_extensions']

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# corsheaders
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
