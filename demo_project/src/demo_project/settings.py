from vprad.conf.defaults import *

USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = 'users.User'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

STATIC_ROOT = os.path.join(os.getcwd(),
                           '_build',
                           'staticfiles')

LOCAL_APPS = [
    'src.users',
    'src.contacts',
    'src.partners',
    'src.demo_project'
]
INSTALLED_APPS = THIRD_PARTY_APPS + VRAD_APPS + LOCAL_APPS

"""AUTH_PASSWORD_VALIDATORS = [
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
]"""

TEST_USER_USERNAME = 'bofh'
TEST_USER_EMAIL = 'bofh@example.com'
TEST_USER_PASSWORD = 'bofhpass'

# region Logging
set_logger('vprad.jinja', level='INFO', propagate=False)
set_logger('vprad', level='DEBUG')
set_logger('src', level='DEBUG')
# endregion
