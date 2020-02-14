from django.contrib.auth import get_user_model

from .models import User
from vprad.actions.decorators import register_model_action
from django.utils.translation import gettext_lazy as _


@register_model_action(model=get_user_model(),
                       name='create',
                       verbose_name=_('Create a new User'),
                       takes_self=False)
def create_user(first_name, last_name, username, email):
    """ Create a new User with a random password. """
    return User.objects.create_user(username=username, email=email,
                                    password=User.objects.make_random_password(),
                                    first_name=first_name, last_name=last_name)


@register_model_action(model=get_user_model(),
                       name='reset_password',
                       verbose_name=_('Reset user password'))
def reset_password(instance: User):
    new_password = User.objects.make_random_password()
    instance.set_password(new_password)
    instance.save()
    return instance
