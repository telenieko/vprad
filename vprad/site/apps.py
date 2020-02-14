import logging

from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from vprad.helpers import autodiscover_modules
from vprad.site.jinja import jinja_globals, jinja_filters

logger = logging.getLogger('vprad.site')


class VSiteConfig(AppConfig):
    name = 'vprad.site'
    label = 'vprad_site'
    verbose_name = gettext_lazy('VPRad Site')

    def ready(self):
        autodiscover_modules('jinja')
        logging.getLogger('vprad.jinja').info("VPRad Jinja ready with %d filters and %d globals",
                                              len(jinja_filters.keys()),
                                              len(jinja_globals.keys()))
        logger.info("VPRad Site ready")
