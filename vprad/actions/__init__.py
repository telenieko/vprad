from vprad.actions.decorators import register_action, register_model_action, transition
from vprad.actions.registry import actions_registry, ActionDoesNotExist, ActionNotAllowed

default_app_config = 'vprad.actions.apps.VActionsConfig'


__all__ = [actions_registry,
           register_action,
           register_model_action,
           transition,
           ActionDoesNotExist,
           ActionNotAllowed]