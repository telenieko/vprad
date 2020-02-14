import collections
import functools
import logging
import typing as t

from django.db import models
from django.db.models.query_utils import DeferredAttribute

from vprad.actions.registry import actions_registry
from vprad.actions.signals import transition_pre, transition_post
from vprad.actions.types import default_full_name, Action
from vprad.helpers import get_icon_for, log_with_caller, call_with_context


logger = logging.getLogger("vprad.actions")


def register_action(name: str = None,
                    full_name: str = None,
                    verbose_name: str = None,
                    icon: str = None,
                    needs_instance: bool = False,
                    conditions: t.Union[t.Callable, t.Iterable[t.Callable]] = None,
                    cls: t.Type = None,
                    **kwargs):
    if not conditions:
        conditions = tuple()
    elif not isinstance(conditions, collections.Iterable):
        conditions = (conditions, )
    else:
        conditions = tuple(conditions)
    if not icon:
        icon = get_icon_for()

    action_kwargs = {
        'name': name,
        'verbose_name': verbose_name,
        'icon': icon,
        'needs_instance': needs_instance,
        'conditions': conditions,
        'cls': cls
    }
    action_kwargs.update(kwargs)

    def _inner(func):
        action_kwargs['function'] = func
        if action_kwargs['name'] is None:
            action_kwargs['name'] = func.__name__
        if action_kwargs['verbose_name'] is None:
            action_kwargs['verbose_name'] = action_kwargs['name'].title()
        action_kwargs['full_name'] = full_name or default_full_name(action_kwargs['name'], func, cls)

        act = Action(**action_kwargs)
        actions_registry.add_action(act)
        log_with_caller(logger, logging.DEBUG, 2,
                        "Registered action '%s'", act.full_name)
        return func

    return _inner


def transition(model: t.Type[models.Model],
               verbose_name: str,
               attached_field: models.Field,
               source, target,
               conditions: t.List[t.Callable] = None,
               icon: str = None):
    """ A transition is a specific kind of action.

    A condition is added requiring `field` to be one of the `source` values,
    then on call it will be updated to target.
    If create_comment is True, a comment will be created.
    """
    if not isinstance(source, t.Iterable):
        source = [source, ]
    if not conditions:
        conditions = []

    def _condition(instance):
        return attached_field.value_from_object(instance) in source

    if isinstance(attached_field, DeferredAttribute):
        attached_field = attached_field.field

    conditions.append(_condition)
    action_kw = {'cls': model,
                 'verbose_name': verbose_name,
                 'needs_instance': True,
                 'icon': icon,
                 'attached_field': attached_field,
                 'conditions': conditions}

    def _inner(func):
        @functools.wraps(func)
        def transition_handler(instance: models.Model,
                               action: Action,
                               request_user,
                               **kwargs):
            current_value = attached_field.value_from_object(instance)
            transition_pre.send(action,
                                instance=instance,
                                current_value=current_value,
                                new_value=target)
            setattr(instance, attached_field.name, target)
            new_value = attached_field.value_from_object(instance)
            retval = call_with_context(func,
                                       instance=instance,
                                       request_user=request_user,
                                       **kwargs)
            transition_post.send(action,
                                 instance=instance,
                                 old_value=current_value,
                                 new_value=new_value)
            return retval

        # noinspection PyTypeChecker
        action_kw['function'] = transition_handler
        action_kw['name'] = func.__name__
        action_kw['full_name'] = default_full_name(action_kw['name'], func, model)
        act = Action(**action_kw)
        actions_registry.add_action(act)
        log_with_caller(logger, logging.DEBUG, 2,
                        "Registered transition '%s'", act.full_name)
        return transition_handler

    return _inner


def register_model_action(model: t.Type[models.Model],
                          name: str = None,
                          verbose_name: str = None,
                          icon: str = None,
                          takes_self: bool = True,
                          attached_field: models.Field = None,
                          conditions: t.Union[t.Callable, t.Iterable[t.Callable]] = None):
    if not icon:
        icon = get_icon_for(model)

    action_kwargs = {
        'name': name,
        'verbose_name': verbose_name or name.title(),
        'icon': icon,
        'conditions': conditions,
        'attached_field': attached_field,
        'needs_instance': takes_self,
        'cls': model,
    }
    return register_action(**action_kwargs)