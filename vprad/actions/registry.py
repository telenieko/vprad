import logging
import typing as t

import attr
from django.db import models
from django.db.models.query_utils import DeferredAttribute

from vprad.actions.types import Action

logger = logging.getLogger("vprad.actions")


class ActionDoesNotExist(Exception):
    pass


class ActionNotAllowed(Exception):
    pass


@attr.s(auto_attribs=True, slots=True)
class VActionsRegistry:
    by_name: t.Dict[str, Action] = attr.ib(default=attr.Factory(dict), repr=False, init=False)

    def find_cls_action(self, cls: t.Type, name: str):
        for act in self.by_name.values():
            if act.name == name and act.cls == cls:
                return act
        raise ActionDoesNotExist("No action named '%s' for class '%s'" % (name, cls))

    def find_action(self, full_name: str):
        """ Find an action on the global registry. """
        if full_name in self.by_name:
            return self.by_name[full_name]
        raise ActionDoesNotExist("No action by the name '%s' in the registry" % full_name)

    def add_action(self, act: Action):
        if act.full_name in self.by_name:
            raise ValueError("The registry already has an action named %s", act.full_name)
        self.by_name[act.full_name] = act

    def get_all_actions_for(self, *,
                            cls=None,
                            instance=None,
                            attached_field: models.Field = '__all__'):
        """ Get available actions for `instance`.

        If `attached_field` is specified then only those attached to the field
            are returned. If it is `None` then unbound actions are returned.
        If `filter_func` it will be called with the action as its only parameter
            and a return value of `False` skips the action.
        """
        if isinstance(attached_field, DeferredAttribute):
            attached_field = attached_field.field

        for act in self.by_name.values():
            if instance and not act.needs_instance:
                continue
            if instance and act.needs_instance and not isinstance(instance, act.cls):
                continue
            if cls and act.needs_instance:
                continue
            if cls and act.cls and not issubclass(cls, act.cls):
                continue
            if attached_field != '__all__' and attached_field != act.attached_field:
                continue
            yield act

    def get_available_actions_for(self, *,
                                  cls=None,
                                  instance=None,
                                  user=None,
                                  attached_field: models.Field = '__all__'):
        for act in self.get_all_actions_for(cls=cls,
                                            instance=instance,
                                            attached_field=attached_field):
            if act.check_conditions(cls=cls, instance=instance, user=user):
                yield act


actions_registry = VActionsRegistry()

