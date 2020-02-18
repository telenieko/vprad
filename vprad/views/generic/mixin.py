import typing as t
from itertools import chain

from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.db import models


class ModelDataMixin:
    """ Simple mixin to enable headline, icon, ... """
    model: t.Type[models.Model]
    icon_class: str = None
    headline: str = None
    headline_subtitle: str = None

    def _get_model_or_object(self):
        """ Return either self.object or self.model

        Allow for the mixin to be used in List and Detail views.
        """
        if hasattr(self, 'get_object'):
            # noinspection PyUnresolvedReferences
            return self.object
        return self.model

    def get_headline(self):
        target = self._get_model_or_object()
        if self.headline:
            v = getattr(target, self.headline)
            return v() if callable(v) else v
        elif isinstance(target, models.Model):
            return str(target)
        # noinspection PyProtectedMember
        return _('%(model_name)s list') % {'model_name': self.model._meta.verbose_name}

    def get_headline_subtitle(self):
        if self.headline_subtitle:
            target = self._get_model_or_object()
            v = getattr(target, self.headline_subtitle)
            return v() if callable(v) else v
        return '-'

    def get_context_data(self, **kwargs):
        kwargs['headline'] = self.get_headline()
        kwargs['headline_subtitle'] = self.get_headline_subtitle()
        return super().get_context_data(**kwargs)


class FieldsAttrMixin:
    """ Simple mixin to enable a `self.fields`

    Fields can be specified by setting `cls.include` tuple,
    or a default will be made from `cls.model` with `cls.exlude`.
    """
    filterset_fields = ()  # Fields for the Filter form if any
    include = ()           # Implicit list of fields to show
    exclude = ()           # Fields to exclude
    _fields = ()           # Calculated list of fields (either `include` or all - exclude).
    default_fields = False  # Indicate if the _fields() are from _make_default_fields.
    model: t.Type[models.Model]
    _always_excluded = ('modified', 'created')

    def _make_default_fields(self):
        opts = self.model._meta
        sortable_private_fields = [f for f in opts.private_fields]
        fields = tuple()
        all_fields = list(chain(opts.concrete_fields, sortable_private_fields, opts.many_to_many))
        exclude = self.exclude
        # GenericForeignKey treatment: If any of the fields that compose the GenericForeignKey
        # or the GenericForeignKey itself is in exclude, then exclude all of them.
        for f in all_fields:
            if isinstance(f, GenericForeignKey):
                my_fields = (f.ct_field, f.fk_field, f.name)
                if any(name in exclude for name in my_fields):
                    exclude += my_fields
        for f in all_fields:
            if f.name not in exclude and f.name not in self._always_excluded:
                fields += (f.name,)
        self.default_fields = True
        return fields

    @property
    def fields(self):
        if not self._fields:
            if self.include:
                self._fields = self.include
            else:
                self._fields = self._make_default_fields()
            if hasattr(self, 'filterset_fields') and self.filterset_fields == '__all__':
                # noinspection PyAttributeOutsideInit
                self.filterset_fields = self._fields
        return self._fields
