import logging
from functools import partial

from vprad.helpers import log_with_caller

logger = logging.getLogger('vprad.jinja.registry')
jinja_globals = {}
jinja_filters = {}


def _registry_decorator(registry, registry_name: str, name: str, replace: bool = False):
    entry_name = name
    if entry_name in registry and not replace:
        raise ValueError("%s already in the %s registry, and replace=False" % (registry_name,
                                                                               entry_name))
    elif entry_name in registry:
        log_with_caller(logger, logging.INFO, 2, "Replacing %s from the %s registry", name, registry_name)

    def _inner(func):
        registry[name] = func
        log_with_caller(logger, logging.DEBUG, 2, "Registered jinja %s: %s", registry_name, name)
        return func
    return _inner


register_global = partial(_registry_decorator, jinja_globals, 'globals')
register_filter = partial(_registry_decorator, jinja_filters, 'filters')
