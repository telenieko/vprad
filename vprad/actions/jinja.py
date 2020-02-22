from django.core.exceptions import FieldDoesNotExist

from vprad.actions import actions_registry
from vprad.site.jinja import register_global


@register_global(name='get_instance_actions')
def get_instance_actions(instance, user):
    return list(actions_registry.get_available_actions_for(instance=instance,
                                                           request_user=user,
                                                           attached_field=None))


@register_global(name='get_instance_field_actions')
def get_instance_field_actions(instance, user, field_name):
    try:
        field = instance._meta.get_field(field_name)
    except FieldDoesNotExist:
        return []
    return list(actions_registry.get_available_actions_for(instance=instance,
                                                           request_user=user,
                                                           attached_field=field))

