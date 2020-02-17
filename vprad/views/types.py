import types
import typing as t
from enum import Enum

import attr
from django.db import models
from django.views import View


class ViewType(Enum):
    LIST = 'list'
    DETAIL = 'detail'
    EMBED_LIST = 'embedded_list'
    EMBED_DETAIL = 'embedded_detail'


@attr.s(auto_attribs=True)
class ViewItem:
    name: str
    urlpaths: t.Any
    view: t.Union[types.FunctionType, View]

    def get_view(self):
        if isinstance(self.view, types.FunctionType):
            return self.view
        return self.view.as_view()

    def get_view_path(self):
        return f"{self.view.__module__}.{self.view.__qualname__}"


@attr.s(auto_attribs=True)
class ModelViewItem:
    model: t.Type[models.Model]
    needs_instance: bool
    create_url: bool
    name: str
    view: t.Union[types.FunctionType, View]

    def get_view(self):
        if isinstance(self.view, types.FunctionType):
            return self.view
        return self.view.as_view()

    def get_view_path(self):
        return f"{self.view.__module__}.{self.view.__qualname__}"

    # noinspection PyMethodMayBeStatic
    def get_pk_field_type(self):
        # TODO: Get the pk field, guess if str, int, etc.
        return str