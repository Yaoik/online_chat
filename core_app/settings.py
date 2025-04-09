from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-fl8s2_@1dea=y_&l)pivo=hi!8w8jq-4&s_rjcv&&x$b0hi&s#", 
)

DEBUG = bool(os.getenv("DEBUG", default=0))

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", default="http://127.0.0.1:8000").split(',')
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", default="*").split(',')
CSRF_COOKIE_DOMAIN = os.getenv("CSRF_COOKIE_DOMAIN", default="")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", default='http://127.0.0.1:8000').split(',')

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'django_extensions',
]

INSTALLED_APPS = [
    *DJANGO_APPS,
    *THIRD_PARTY_APPS,
    'common',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core_app.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'core_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', default='postgres_name'),
        'USER': os.getenv('POSTGRES_USER', default='postgres_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', default='postgres_password'),
        'HOST': os.getenv('POSTGRES_HOST', default='localhost'),
        'PORT': os.getenv('POSTGRES_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "users.User"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if DEBUG else "ERROR",
    },
    "loggers": {
        "django.db": {
            "handlers": ["console"],
            "level": "INFO" if DEBUG else "ERROR",
            "propagate": False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'TITLE',
    'DESCRIPTION': 'DESCRIPTION',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', "redis://redis:6379/0") 
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', "redis://redis:6379/0") 
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_IGNORE_RESULT = False
CELERY_TASK_RETRY_COUNTDOWN = 30
CELERY_EAGER_PROPAGATES = DEBUG
CELERY_RESULT_EXPIRES = 60 * 60