"""
Set the LDAP URL to the correct server for this environment.  Modify the remaining settings to run the django app.
"""

import os
from django.urls import reverse
import urllib

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# USE_X_FORWARDED_HOST = True

LDAP_URL = "gisapps.aroraengineers.com"
# LDAP_URL = "renoairport.net"

if LDAP_URL == "gisapps.aroraengineers.com":
    # always run AD check against AD in the cloud so set this as default
    PYTHON_PATH = r"C:\ProgramData\Anaconda3\envs\rtaa_gis"
    if "rtaa_gis_django" in os.path.abspath(__file__).split("\\"):
        FORCE_SCRIPT_NAME = "/rtaa_gis/"
    elif "rtaa_gis_production" in os.path.abspath(__file__).split("\\"):
        FORCE_SCRIPT_NAME = "/rtaa_prod/"
    else:
        # the code directory is on a local server not IIS
        FORCE_SCRIPT_NAME = ""
        PYTHON_PATH = r"C:\Program Files (x86)\Anaconda3\envs\rtaa_gis\python.exe"

    FILE_APP_TOP_DIRS = [r"c:\inetpub\ftproot\gisapps\gissetup"]
    IIS_APP_ROOT = r"C:\inetpub\wabapps"
    SERVER_URL = "https://{}".format(LDAP_URL)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_USE_TLS = False
    EMAIL_HOST = "aspmx.l.google.com"
    EMAIL_PORT = 25
    # EMAIL_HOST_USER = ""
    # EMAIL_HOST_PASSWORD = ""

elif LDAP_URL == "renoairport.net":
    if "rtaa_gis_django_testing" in os.path.abspath(__file__).split("\\"):
        FORCE_SCRIPT_NAME = "/applications_test/"
    elif "rtaa_gis_django" in os.path.abspath(__file__).split("\\"):
        FORCE_SCRIPT_NAME = "/applications/"

    PYTHON_PATH = r"C:\inetpub\Anaconda3\envs\rtaa_gis\python.exe"
    FILE_APP_TOP_DIRS = [r"\\renofs2\groups\Engineering\Drawings\Std", r"\\renofs2\groups\Engineering\Drawings\Rno"]
    IIS_APP_ROOT = r"C:\inetpub\apps"
    SERVER_URL = "https://gis.{}".format(LDAP_URL)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_USE_TLS = False
    EMAIL_HOST = "mail.renoairport.net"
    EMAIL_PORT = 25
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ARCPY_PATH = r"C:\Python27\ArcGIS10.5\python.exe"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400

APPEND_SLASH = False

# This setting gets used in templates to build correct hyperlinks
if DEBUG:
    FORCE_SCRIPT_NAME = '/'

MEDIA_URL = FORCE_SCRIPT_NAME + 'media/'
STATIC_URL = FORCE_SCRIPT_NAME + 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Application definition
ROOT_URLCONF = r'rtaa_gis.urls'
LOGIN_URL = r'login'

SWAGGER_SETTINGS = {
    'JSON_EDITOR': True,
    'LOGIN_URL': 'rest_framework:login',
    'LOGOUT_URL':  'rest_framework:logout'
}

LOGIN_REDIRECT_URL = FORCE_SCRIPT_NAME

FCGI_DEBUG = True
FCGI_LOG = True
FCGI_LOG_PATH = os.path.join(BASE_DIR, "logs")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'bo0*s)^co9abj49*kpp(+91&98v25=0s3#3bv-3-l(2hg9q!5c'

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False

# CSRF_COOKIE_DOMAIN = ['.renoairport.net', '.aroraengineers.com']
CSRF_TRUSTED_ORIGINS = ('localhost:3003', 'gisapps.aroraengineers.com:3344', 'localhost:3344', 'gisapps.aroraengineers.com',
                        'gisapps.aroraengineers.com:443', 'gis.renoairport.net:443', 'localhost')

CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False

CORS_ALLOW_CREDENTIALS = True
CORS_REPLACE_HTTPS_REFERRER = False
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'https://gisapps.aroraengineers.com',
    'localhost:3003',
    'localhost:3001',
    'https://gisapps.aroraengineers.com:3344',
    'localhost:3344',
    'https://gis.renoairport.net',
    'localhost',
    '127.0.0.1:8080',
    'localhost:3000',
    'localhost:8080'
)
CORS_ALLOW_HEADERS = (
    # 'content-range',
    'x-requested-with',
    'authorization',
    'content-type',
    'x_csrftoken'
)

CORS_EXPOSE_HEADERS = (
    'x-requested-with',
    # 'content-type',
    # 'content-range',
    # 'accept',
    # 'origin',
    'authorization',
    'x_csrftoken',
)

ALLOWED_HOSTS = [
    'gisapps.aroraengineers.com',
    '10.0.0.5',
    'gis.renoairport.net',
    'localhost:3344',
    '127.0.0.1',
    '172.72.118.217',
    # '13.90.210.35'
]

if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    CORS_REPLACE_HTTPS_REFERER = False
    CORS_ORIGIN_ALLOW_ALL = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework_swagger',
    'crispy_forms',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'home.apps.HomeConfig',
    'fileApp.apps.FileAppConfig',
    'cloudSync.apps.CloudsyncConfig',
    'printTool.apps.PrinttoolConfig',
    'analytics.apps.AnalyticsConfig',
    'diagrams.apps.DiagramsConfig',
    'lpm.apps.LpmConfig',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.auth.middleware.PersistentRemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'rtaa_gis.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'sql_server.pyodbc',
    #     'NAME': 'GIS_Web',
    #     'HOST': 'gis.renoairport.net',
    #     'USER': 'gis',
    #     'PASSWORD': "GIS@RTAA123!",
    #     'OPTIONS': {
    #         'driver': 'ODBC Driver 13 for SQL Server'
    #      }
    #  },
    # 'postGres': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'rtaa_DRF',
    #     'USER': 'postgres',
    #     'PASSWORD': 'AroraGIS123',
    #     'HOST': '127.0.0.1',
    #     'PORT': '5432'
    # },
    'default': {
         'ENGINE': 'django.db.backends.sqlite3',
         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
     }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


REST_FRAMEWORK = {

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'PAGE_SIZE': 15,
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        # 'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.OrderingFilter',
        # 'rest_framework.filters.DjangoFilterBackend',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    )
}

LOGGING = {
    # TODO - setup the email logging for running on IIS
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'standard'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': "ERROR",
            'filename': os.path.join(BASE_DIR, 'logs/django_log.log'),
            'maxBytes': 1024*1024*10,
            'backupCount': 5,
            'formatter': 'standard'
        }
    },
    'loggers': {
        'analytics': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'diagrams': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'cloudSync': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'lpm': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'fileApp': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'printTool': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'home': {
            'handlers': ['console', 'file'],
            'level': "ERROR",
            'propogate': True
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': "ERROR"
        },
        'django.security.DisallowedHost': {
            'handlers': ['file'],
            'propagate': False,
        }
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
