import inspect
import traceback
from collections import OrderedDict
from typing import Type, Dict

import attr
from attr.validators import instance_of as attr_instance_of, optional as attr_optional
from braces.views import SetHeadlineMixin
from django import forms
from django.db import models
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import path
from django.utils.decorators import classonlymethod
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin

from . import actions_registry
from .forms import AnnotationFormFactory
from .types import Action
from ..helpers import get_url_for


@attr.s(auto_attribs=True)
class ActionViewHelper:
    action: Action = attr.ib(validator=attr_instance_of(Action))
    object: models.Model = attr.ib(validator=attr_optional(attr_instance_of(models.Model)))
    action_form: forms.ModelForm = attr.ib(default=None)
    form_classes: Dict[str, Type[forms.Form]] = attr.ib(default=attr.Factory(dict))

    @property
    def verbose_name(self):
        return self.action.verbose_name

    def __attrs_post_init__(self):
        factory = AnnotationFormFactory(name=self.action.name,
                                        verbose_name=self.action.verbose_name,
                                        instance=self.object,
                                        method=self.action.function,
                                        model=self.action.cls)
        self.action_form = factory.form_class
        self.form_classes = factory.get_form_classes()

    def trigger_action(self, request, request_forms: Dict[str, forms.Form]):
        data = {'request_user': request.user,
                'instance': self.object}
        for name, form in request_forms.items():
            if name == '_method':
                data.update(form.cleaned_data)
            else:
                data[name] = form
        return self.action.call(**data)


#@register_view(name='action', urlpaths=["action/<str:action_name>",
#                                        "action/<str:action_name>/<str:pk>"])
class ActionView(SetHeadlineMixin, SingleObjectMixin, TemplateView):
    template_name = 'vprad/actions/action.jinja.html'
    helper: ActionViewHelper = None
    object: models.Model = None
    forms = Dict[str, forms.Form]
    action: Action = None

    def get_headline(self):
        return self.helper.action.verbose_name

    @classonlymethod
    def as_view(cls, action: Action, **initkwargs):
        initkwargs['model'] = action.cls
        initkwargs['action'] = action
        return super().as_view(**initkwargs)

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if pk:
            self.object = self.get_object()
        action = self.action
        if not action.check_conditions(instance=self.object, user=request.user):
            return HttpResponseForbidden("Action not available")
        self.helper = ActionViewHelper(action, self.object)
        self.init_forms()
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self, name):
        """Return the initial data for a form."""
        prefix = f"{name}-"
        initial = {}
        for k, v in self.request.GET.items():
            if k.startswith(prefix):
                k = k[len(prefix):]
                initial[k] = v
        return initial

    def get_form_kwargs(self, name, form_class):
        """Return the keyword arguments for instantiating the form."""
        kwargs = {
            'prefix': name,
            'initial': self.get_initial(name)
        }
        sig = inspect.signature(form_class.__init__)
        if 'instance' in sig.parameters:
            kwargs['instance'] = self.object
        if 'target_object' in sig.parameters:
            kwargs['target_object'] = self.object

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
            if issubclass(form_class, forms.ModelForm):
                kwargs['instance'] = self.object
        return kwargs

    def init_forms(self):
        self.forms = OrderedDict()
        for name, form_class in self.helper.form_classes.items():
            self.forms[name] = form_class(**self.get_form_kwargs(name, form_class))

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        one_invalid = False
        for form in self.forms.values():
            one_invalid = not form.is_valid() or one_invalid
        if one_invalid:
            return self.forms_invalid()
        return self.forms_valid() or redirect(self.get_next())

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.object
        kwargs['transition_name'] = self.helper.verbose_name
        kwargs['forms'] = self.forms
        return super().get_context_data(**kwargs)

    def forms_invalid(self):
        """ At least one form was invalid. """
        return self.render_to_response(self.get_context_data())

    def forms_valid(self):
        res = self.helper.trigger_action(self.request, self.forms)
        return get_url_for(res)

    def get_next(self):
        if 'next' in self.request.GET:
            return self.request.GET['next']
        return get_url_for(self.object) or 'home'

