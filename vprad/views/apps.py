import logging

from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from vprad.helpers import autodiscover_modules
from vprad.views.registry import views_registry, model_views_registry

logger = logging.getLogger('vprad.views')


class VViewsConfig(AppConfig):
    name = 'vprad.views'
    label = 'vprad_views'
    verbose_name = gettext_lazy('VPRad Views')

    def ready(self):
        # noinspection PyUnresolvedReferences
        import vprad.views.defaults
        autodiscover_modules('views')
        logger.info("VPRad Views ready with %d views and %d model views",
                    len(views_registry.keys()),
                    len(model_views_registry.keys()))
