"""
Development settings - unsuitable for production
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
DATABASES['default']['HOST'] = 'localhost'

# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Celery - Use eager mode for development (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_ROOT = BASE_DIR / "media"

# Logging
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['apps']['level'] = 'INFO'