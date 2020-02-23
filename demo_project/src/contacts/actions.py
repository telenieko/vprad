from django.utils.translation import gettext_lazy as _
from src.contacts.models import ContactEmailAddress
from vprad.actions import register_model_action


@register_model_action(model=ContactEmailAddress,
                       name='create',
                       verbose_name=_('Add an email address'),
                       takes_self=False)
def create_email_address(parent,
                         internal_note,
                         email):
    e = ContactEmailAddress.objects.create(parent=parent,
                                           internal_note=internal_note,
                                           email=email)
    print(e)
    return parent