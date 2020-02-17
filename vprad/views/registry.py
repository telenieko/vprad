import logging
import typing as t

from django.db import models
from django.urls import path

from vprad.views.helpers import get_model_url_name, get_model_url_path
from vprad.views.types import ModelViewItem, ViewItem, ViewType

logger = logging.getLogger("vprad.views")

views_registry = {}
model_views_registry = {}


def register_model_view(*,
                        model: t.Type[models.Model],
                        needs_instance: bool,
                        view_type: t.Union[str, ViewType] = None,
                        replace: str = None,
                        name: str = None):
    if not name:
        name = get_model_url_name(model, view_type)
    view_type = view_type.value if isinstance(view_type, ViewType) else view_type
    existing = model_views_registry.get(name, None)
    if existing and (not replace or existing.get_view_path() != replace):
        raise ValueError("A model view with name '%s' already registered" % name)
    elif existing:
        logger.info("Model view '%s' is being replaced", existing.get_view_path())

    def _inner(fn):
        model_views_registry[name] = ModelViewItem(model=model,
                                                   name=name,
                                                   needs_instance=needs_instance,
                                                   create_url=not view_type.startswith('embedded_'),
                                                   view=fn)
        logger.debug("Registered model view: '%s' for '%s.%s' from '%s'",
                     name,
                     model._meta.app_label, model._meta.model.__name__,
                     model_views_registry[name].get_view_path())
        return fn

    return _inner


def register_view(*,
                  name: str,
                  urlpaths: t.Union[str, t.Tuple[str]],
                  replace: str = None):
    if type(urlpaths) == str:
        urlpaths = (urlpaths,)
    existing = views_registry.get(name, None)
    if existing and (not replace or existing.get_view_path() != replace):
        raise ValueError("A view with name '%s' already registered" % name)
    elif existing:
        logger.info("View '%s' is being replaced", existing.get_view_path())

    def _inner(fn):
        views_registry[name] = ViewItem(name=name, urlpaths=urlpaths, view=fn)
        logger.debug("Registered view: '%s' from '%s'", name, views_registry[name].get_view_path())
        return fn

    return _inner
