from pathlib import Path
import os
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-)m^_rzn5fu!@w^69!ixov$sy@6ia+dr!i+*@l092gaj)l%*(h@')

# SECURITY WARNING: don't run with debug turned on in production!
# Read DEBUG from environment so production can set DEBUG=False while
# development keeps DEBUG=True by default. Use python-decouple's `config`
# which is already imported in this settings file.
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'resumebuilder',
    'pathpilot',
    'feed360',
    'ATS',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

# Add WhiteNoise only in production
if not DEBUG:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'core.middleware.NoCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Support a single DATABASE_URL for production (Supabase/Postgres) while
# falling back to sqlite for local development. If DATABASE_URL is present
# it will be used as the primary `default` database and sqlite will be
# available under the `sqlite` alias as a secondary DB.
from urllib.parse import urlparse

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Parse DATABASE_URL like postgres://user:pass@host:port/dbname
    url = urlparse(DATABASE_URL)
    DB_NAME = url.path[1:]
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': DB_NAME,
            'USER': url.username or '',
            'PASSWORD': url.password or '',
            'HOST': url.hostname or '',
            'PORT': url.port or '',
            'OPTIONS': {},  # db_options should be {} for localhost
        },
        'sqlite': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
            'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
            'USER': config('DB_USER', default=''),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default=''),
            'PORT': config('DB_PORT', default=''),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))

# Use different STATIC_ROOT for production vs development
if DEBUG:
    # In development, keep the original setup
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
else:
    # In production, use a separate directory
    STATIC_ROOT = config('STATIC_ROOT', default=os.path.join(BASE_DIR, 'staticfiles'))
    
    # Additional locations of static files (only in production)
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
    
    # Simplified static file serving with whitenoise (only in production)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings to persist login after refresh
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

LOGIN_REDIRECT_URL = 'dash'
LOGIN_URL = 'login'

# Email settings for Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='website2k5@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='oqto rbin gdwz ydnw')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='website2k5@gmail.com')

LOGOUT_REDIRECT_URL = 'dash'
LOGOUT_URL="logout"

# Security Settings for Production
if not DEBUG:
    # HTTPS Settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Other Security Settings
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Proxy Settings (if using a reverse proxy like nginx)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
