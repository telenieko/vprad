import typing as t

from django.db import models


def get_model_url_name(model: t.Type[models.Model],
                       action: str = None):
    n = "%s_%s" % (model._meta.app_label, model._meta.model_name,)
    if action:
        n += "_%s" % action
    return n


def get_model_url_path(model: t.Type[models.Model],
                       action: str = None,
                       pk_field: str = None):
    # noinspection PyProtectedMember
    urlpath = "%s/%s" % (model._meta.app_label,
                         model._meta.model_name)
    if pk_field:
        # TODO: Get the pk field, guess if str, int, etc.
        pk_field = model._meta.get_field(pk_field)
        pk_field_type = str.__name__
        urlpath += "/<%s:pk>" % pk_field_type
    if action:
        urlpath += "/" + action
    return urlpath
