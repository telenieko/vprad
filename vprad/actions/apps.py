import logging

from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from vprad.actions import actions_registry
from vprad.helpers import autodiscover_modules

logger = logging.getLogger('vprad.actions')


class VActionsConfig(AppConfig):
    name = 'vprad.actions'
    label = 'vprad_actions'
    verbose_name = gettext_lazy('VPRad Actions')

    def ready(self):
        autodiscover_modules('actions')
        logger.info("VPRad Actions ready with %d actions", len(actions_registry.by_name.keys()))
