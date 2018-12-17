import os
SECRET_KEY = 'fake-key'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_APP_TOP_DIRS = [r"\\renofs2\groups\Engineering\Drawings\Std", r"\\renofs2\groups\Engineering\Drawings\Rno"]
ARCPY_PATH = r"C:\Python27\ArcGIS10.4\python.exe"
LDAP_URL = "gisapps.aroraengineers.com"
IIS_APP_ROOT = r"C:\inetpub\wabapps"
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
    'fileApp.apps.FileAppConfig',
    'home.apps.HomeConfig',
    'cloudSync.apps.CloudsyncConfig',
    'printTool.apps.PrinttoolConfig',
    'lpm.apps.LpmConfig'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
ROOT_URLCONF = r'rtaa_gis.urls'
LOGIN_URL = r'login/'
LOGIN_REDIRECT_URL = r'/'
