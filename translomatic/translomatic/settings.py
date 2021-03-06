"""
Django settings for translomatic project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import django

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from configparser import RawConfigParser
parser = RawConfigParser()

APPLICATION_ROOT = os.path.abspath(os.path.dirname(__file__))
parser.readfp(open(os.path.join(APPLICATION_ROOT, 'local.ini')))


#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



SECRET_KEY = parser.get('global', 'secret_key')



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


MEDIA_ROOT = parser.get('global', 'media_root')
#ROSETTA_EXCLUDE_PATHS = '/Users/jaclu/cloud/Dropbox/proj/europeana/translomatic/apps/portal_trans'

#LOCALE_PATHS = (
#    '/Users/jaclu/cloud/Dropbox/proj/europeana/translomatic/apps/portal_trans/locale',
#)



# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rosetta',
    'apps.portal_trans'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'translomatic.urls'




TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [MEDIA_ROOT],
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

WSGI_APPLICATION = 'translomatic.wsgi.application'




# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': parser.get('global', 'database_name')
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
#LANGUAGE_CODE = 'de'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/



TEMPLATE_DEBUG = True







##ROOT_URLCONF = 'multilingo.urls'

##PORTAL_PREFIX = 'portal'





# The path to local media aditions, all content hear will be pushed to the
# production server and can be used for aditional css/js/imgs etc
#
##MEDIA_FILE_PATH = 'sp'

#
# Where generated content for submission should be created
# this path will be cleared before each submit, so please dont point it to
# something like your home dir
#
# [[ If you havent read this and come to me with issues,  ]]
# [[ I will laught at you and point to this comment...    ]]
#
# As always keep your backups current!  ]]
#
##SUBMIT_PATH = '/tmp/submit'

#
# Normally progress is not displayed when translations are
# processed by the webserver, when fronted by apache
# apache can not tolerated anything to stdout
# enable this in test environs to get translation progess
#
##TRANSLATIONS_ALLWAYS_SHOW_PROGRESS = False


#
#=====================   Europeana languages settings   =======================
#

STATIC_URL = '/static/'
#STATIC_ROOT = '/Users/jaclu/proj/europeana/portal/portal2/src/main/webapp/'





# All supported languages
LANGUAGES = (
    ('en', 'English (eng)'),
    ('eu', 'Basque (eus)'),
    ('bg', 'Bulgarian (bul)'),
    ('ca', 'Catalan (ca)'),
    ('cs', 'Czech (cze/cse)'),
    ('da', 'Dansk (dan)'),
    ('de', 'Deutsch (deu)'),
    ('et', 'Eesti (est)'),
    ('es', 'Espanol (esp)'),
    ('fr', 'Francais (fre)'),
    ('gl', 'Galego (glg)'),     # Galician
    ('el', 'Greek (ell/gre)'),
    ('hr', 'Hrvatski (hrv)'),  # Croatian <- new!
    ('ga', 'Irish (gle)'),
    ('is', 'Islenska (ice)'),
    ('it', 'Italiano (ita)'),
    ('lv', 'Latvian (lav)'),
    ('lt', 'Lithuanian (lit)'),
    ('hu', 'Magyar (hun)'),
    ('mt', 'Malti (mlt)'),
    ('nl', 'Nederlands (dut)'),
    ('no', 'Norsk (nor)'),
    #('nb', 'Norsk Bokmal (nob)'),
    ('pl', 'Polski (pol)'),
    ('pt', 'Portuguese (por)'),
    ('ro', 'Romanian (rom'),
    ('ru', 'Russian (rus)'),
    ('sl', 'Slovenian (slv)'),
    ('sk', 'Slovkian (slo)'),
    ('fi', 'Suomi (fin)'),
    ('sv', 'Svenska (sve/swe)'),
    ('uk', 'Ukrainian (ukr)'),
)


# just the lang keys for quick lookups
LANGUAGES_DICT = {}
for _k, _lbl in LANGUAGES:
    LANGUAGES_DICT[_k] = _lbl
# clean up of temp vars
del _k, _lbl