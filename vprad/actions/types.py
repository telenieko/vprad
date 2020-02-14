import types
import typing as t

import attr
from attr.validators import instance_of as attr_instance_of, optional as attr_optional
from django.db import models
from django.db.models import Field
from django.shortcuts import resolve_url
from django.urls import reverse

from vprad.actions.signals import action_pre, action_post
from vprad.helpers import call_with_context


@attr.s(auto_attribs=True, slots=True, frozen=True)
class Action:
    """ An Action definition
    """
    name: str = attr.ib(validator=attr_instance_of(str), repr=False)
    full_name: str = attr.ib(validator=attr_instance_of(str), repr=True)
    verbose_name: str = attr.ib(repr=False)
    icon: str = attr.ib(repr=False)
    function: types.FunctionType = attr.ib(repr=False)
    conditions: t.Tuple[t.Callable] = attr.ib(repr=False,
                                              validator=attr_instance_of(tuple),
                                              converter=tuple)
    needs_instance: bool = attr.ib(validator=attr_instance_of(bool),
                                   repr=True)

    cls: t.Type[models.Model] = attr.ib(repr=False, default=None)
    attached_field: t.Optional[Field] = attr.ib(validator=attr_optional(attr_instance_of(Field)),
                                                default=None)

    full_path: str = attr.ib(default=attr.Factory(
        lambda self: f"{self.function.__module__}.{self.function.__qualname__}",
        takes_self=True
    ), init=False)

    def get_absolute_url(self, instance=None, next_url=None):
        if self.needs_instance and not instance:
            raise ValueError("Action %s (%s) needs an instance" % (self.full_name, self.full_path))
        if instance:
            return reverse(self.full_name, args=[instance.pk]) + (f"?next={next_url}" if next_url else '')
        return reverse(self.full_name) + (f"?next={next_url}" if next_url else '')

    def check_conditions(self, cls=None, instance=None, user=None):
        if instance and not self.needs_instance:
            return False
        elif self.needs_instance and not instance:
            return False
        ctx = {'user': user,
               'action': self,
               'cls': cls,
               'instance': instance,
               'self': instance}
        for c in self.conditions:
            if not call_with_context(c, **ctx):
                return False
        return True

    def call(self, **kwargs):
        action_pre.send(self, **kwargs)
        if 'action' not in kwargs:
            kwargs['action'] = self
        if self.cls and 'cls' not in kwargs:
            kwargs['cls'] = self.cls
        retval = call_with_context(self.function, **kwargs)
        kwargs.pop('action')  # don't send it with the signal.
        action_post.send(self, **kwargs)
        return retval


def default_full_name(name, func, cls):
    """ Create a default full_name for the function `func`. """
    if cls and issubclass(cls, models.Model):
        return "%s_%s_%s" % (cls._meta.app_label, cls._meta.model_name, name)
    modname = func.__module__ if func.__module__ else '__nomodule'
    for v in modname.split('.')[::-1]:
        if v != 'actions':
            modname = v
            break
    return "%s_%s" % (modname, name)