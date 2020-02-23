from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
# noinspection PyProtectedMember
from django.forms import MultiValueField, CharField, HiddenInput, MultiWidget
from django.forms.models import apply_limit_choices_to_to_formfield, ModelChoiceField

from vprad.models import AutocompleteMixin


class GenericForeignKeyField(CharField):
    """ Simple field to pass values to a GenericForeignKey

    It is used by the create actions to pass in the value of a GenericForeignKey.
    """
    widget = HiddenInput
    hidden_widget = HiddenInput

    def clean(self, value):
        delim = value.find('/')
        ct_pk, pk = value[:delim], value[delim+1:]
        ct = ContentType.objects.get(pk=ct_pk)
        return ct.model_class().objects.get(pk=pk)


def get_formfield_for_field(field: models.Field):
    kwargs = {}
    formfield = None
    if isinstance(field, (models.ForeignKey,
                          models.OneToOneField)) and issubclass(field.related_model, AutocompleteMixin):
        kwargs['widget'] = field.related_model.get_fk_widget()
    if isinstance(field, GenericForeignKey):
        fk_field = field.model._meta.get_field(field.fk_field)
        formfield = GenericForeignKeyField(required=not fk_field.null, **kwargs)
    if not formfield:
        formfield = field.formfield(**kwargs)
    apply_limit_choices_to_to_formfield(formfield)
    return formfield
