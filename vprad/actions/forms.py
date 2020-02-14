import inspect
import typing as t
from collections import OrderedDict

import attr
from django.db import models
from django.forms import forms, model_to_dict
# noinspection PyProtectedMember
from django.forms.models import apply_limit_choices_to_to_formfield, ModelForm
from django.utils.translation import gettext_lazy as _


class ActionForm(forms.Form):
    verbose_name = _('Action')
    fields = {}

    def __init__(self, instance=None, *args, **kwargs):
        initial = kwargs.pop('initial') if 'initial' in kwargs else {}
        if instance is None:
            self.instance = None
        else:
            self.instance = instance
            object_data = model_to_dict(instance, self.fields.keys(), None)
            initial.update(object_data)
        super().__init__(*args, initial=initial, **kwargs)


@attr.s(auto_attribs=True)
class AnnotationFormFactory:
    """ Creates forms from the annotations of a method.

    The method might have:
        - Reserved arguments, which are ignored (self, instance, ...)
        - Argument with type hints and a form field as the default value which
            is used as is.
        - Arguments whose name is a field_name of the model linked to the class,
            then the field's formfield is used. If a default value is provided
            it will be passed on to initial.

    The defaults might be a callable, in which case it is called.
    """
    # Those are not considered (because we supply values for them):
    reserved_words = ['self',
                      'request_user',
                      'instance',
                      'action',
                      'args',
                      'kwargs']

    name: str
    verbose_name: str
    instance: models.Model
    method: t.Callable
    base_form_class: ActionForm = attr.ib(default=ActionForm)
    model: t.Type[models.Model] = attr.ib(default=None)

    def __attrs_post_init__(self):
        params = self._field_parameters()
        self.extra_form_classes = self._get_extra_form_classes(params)
        self.form_class = self._get_action_form(params)

    # noinspection PyMethodMayBeStatic
    def _get_formfield(self, field: models.Field):
        kwargs = {}
        # if isinstance(field, models.ForeignKey) and hasattr(field.related_model, 'get_default_fk_widget'):
        #     kwargs['widget'] = field.related_model.get_default_fk_widget()
        formfield = field.formfield(**kwargs)
        apply_limit_choices_to_to_formfield(formfield)
        return formfield

    def _field_parameters(self):
        cls = self.model
        method = self.method
        params = {}
        model_fields = {}
        if cls and issubclass(cls, models.Model):
            model_fields = {f.name: f for f in cls._meta.get_fields()}
        data: inspect.Parameter
        for name, data in inspect.signature(method, follow_wrapped=True).parameters.items():
            if name in self.reserved_words:
                continue
            elif name in params:
                continue
            ptype = data.default
            if data.default != data.empty and isinstance(data.default, forms.Field):
                params[name] = data.default
            elif inspect.isclass(ptype) and issubclass(ptype, (forms.Form,
                                                               ModelForm)):
                params[name] = ptype
            elif name in model_fields:
                formfield = self._get_formfield(model_fields[name])
                if data.default != data.empty:
                    formfield.initial = data.default() if callable(data.default) else data.default
                    formfield.required = False
                params[name] = formfield
            else:
                raise ValueError("Cannot process argument named '%s' of '%s'" % (name, method))
        return params

    def get_form_classes(self):
        form_classes = self.extra_form_classes.copy()
        if self.form_class:
            form_classes['_method'] = self.form_class
            form_classes.move_to_end('_method', last=False)
        return form_classes

    # noinspection PyMethodMayBeStatic
    def _get_extra_form_classes(self, params):
        classes = OrderedDict()
        for name, value in params.items():
            if inspect.isclass(value) and issubclass(value, (forms.Form,
                                                             ModelForm)):
                classes[name] = value
        return classes

    def _get_action_form(self, params) -> t.Optional[t.Type[ActionForm]]:
        if len(params.keys()) == 0:
            return None
        base = self.base_form_class
        class_name = self.name.title() + 'ActionForm'

        attrs = {'verbose_name': self.verbose_name}
        for name, value in params.items():
            if isinstance(value, forms.Field):
                attrs[name] = value
        # noinspection PyTypeChecker
        return type(base)(class_name, (base,), attrs)
