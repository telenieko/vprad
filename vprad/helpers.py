import copy
import inspect
import logging
import typing as t
import types
from functools import partial
from importlib import import_module
from os.path import relpath
from typing import Sequence

from django.apps import AppConfig
from django.db import models
from django.urls import reverse, NoReverseMatch, clear_url_caches as _clear_url_caches
from django.utils.module_loading import module_has_submodule

from vprad.views.helpers import get_model_url_name

helpers_logger = logging.getLogger(__name__)


def get_url_for(what=None):
    if hasattr(what, 'get_absolute_url'):
        return what.get_absolute_url()
    if isinstance(what, models.Model):
        url_name = get_model_url_name(what.__class__, 'detail')
        try:
            return reverse(url_name, args=[what.pk, ])
        except NoReverseMatch:
            pass
    return None


def get_icon_for(what=None):
    if getattr(what, 'icon_class', None):
        return what.icon_class
    elif hasattr(what, 'model') and getattr(what.model, 'icon_class', None):
        return what.model.icon_class
    return 'dot circle'


def log_with_caller(logger: logging.Logger,
                    log_level: int,
                    stack_level: int,
                    message: str,
                    *args, **kwargs):
    """ Logs a message including information of the caller.

    The caller printet is that `stack_level` frames above us.
    """
    frame_info: inspect.FrameInfo = inspect.stack()[stack_level]
    filename = relpath(frame_info.filename)

    prefix = f"{filename}:{frame_info.lineno}:{frame_info.function} "
    logger.log(log_level, prefix + message, *args, **kwargs)


log_warning = partial(log_with_caller, helpers_logger, logging.WARNING)


def call_with_context(func: t.Callable,
                      **kwargs):
    """ Helper for calling functions with unkown *args/**kwargs.

    This function will use inspect.signature to see what parameters
    `func` takes and call it with those parameters taken from `kwargs`.
    """
    params = inspect.signature(func, follow_wrapped=False).parameters
    funckw = {}
    for name, param in params.items():
        if name in ['args', 'kwargs']:
            continue
        if name not in kwargs and param.default == inspect.Parameter.empty:
            raise TypeError("Missing '%s' parameter to call '%s'" % (
                name,
                f"{func.__module__}.{func.__qualname__}",
            ))
        if name in kwargs:
            value = kwargs.pop(name)
            if param.annotation and param.annotation != inspect.Parameter.empty:
                if not isinstance(value, param.annotation):
                    log_warning(2, "'%s' expects '%s' to be of type '%s' not '%s'",
                                f"{func.__module__}.{func.__qualname__}",
                                name, param.annotation, type(value))
            funckw[name] = value
    if 'kwargs' in params.keys():
        funckw.update(kwargs)
    return func(**funckw)


def autodiscover_modules(*args, **kwargs):
    """ Like django.utils.module_loading.autodiscover_modules

    It just ignores any app that is not in VRAD_APPS or LOCAL_APPS
    """
    from django.apps import apps
    from django.conf import settings

    vrad_apps = settings.VRAD_APPS + settings.LOCAL_APPS
    for app_config in apps.get_app_configs():
        if not isinstance(app_config, AppConfig):
            continue
        if not app_config.name in vrad_apps:
            continue
        for module_to_search in args:
            # Attempt to import the app's module.
            # noinspection PyBroadException
            try:
                import_module('%s.%s' % (app_config.name, module_to_search))
            except Exception:
                # Decide whether to bubble up this error. If the app just
                # doesn't have the module in question, we can ignore the error
                # attempting to import it, otherwise we want it to bubble up.
                if module_has_submodule(app_config.module, module_to_search):
                    raise


class LazyClosureSequence(Sequence):
    """ Sequence that gets items from a callable.

    The callable is called on first item access, and its cache
    can be reset with `self`.`reset_cache()`
    This is mainly used in URLconf's so they can be changed dynamically during testing.
    """
    _cached = None

    def __init__(self, get_items):
        self._get_items = get_items

    def reset_cache(self):
        self._cached = None

    @property
    def _values(self):
        if not self._cached:
            self._cached = self._get_items()
        return self._cached

    def __getitem__(self, i):
        return self._values[i]

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return repr(self._values)


def clear_url_caches():
    from vprad.actions import urls as actions_urls
    from vprad.views import urls as views_urls
    actions_urls.urlpatterns.reset_cache()
    views_urls.urlpatterns.reset_cache()
    _clear_url_caches()
