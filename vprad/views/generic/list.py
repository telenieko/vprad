import django_tables2 as tables
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse, NoReverseMatch
from django_filters.views import FilterView
from django_tables2 import Table

from vprad.helpers import get_url_for
from vprad.views.generic.embedding import VEmbeddableMixin
from vprad.views.generic.mixin import FieldsAttrMixin, ModelDataMixin
from vprad.views.helpers import get_model_url_name


class VTableBase(Table):
    id = tables.Column(linkify=lambda record: get_url_for(record))


class VListViewBase(FieldsAttrMixin,
                    ModelDataMixin,
                    tables.SingleTableMixin,
                    FilterView):
    template_name = 'vprad/views/list/object_list.html'
    paginate_by = 10
    table_base = VTableBase

    def get_table_class(self):
        """
        Return the class to use for the table.
        """
        if self.table_class:
            return self.table_class
        if self.model:
            return tables.table_factory(self.model, table=self.table_base,
                                        fields=self.fields)

        raise ImproperlyConfigured(
            "You must either specify {0}.table_class or {0}.model".format(type(self).__name__)
        )

    def get_context_data(self, **kwargs):
        kwargs['model'] = self.model
        return super().get_context_data(**kwargs)


class VListView(VListViewBase):
    pass


class EmbeddedTableBase(VTableBase):
    class Meta:
        orderable = False
        attrs = {
            'class': 'ui very basic  celled table'
        }


class VEmbeddableListView(VEmbeddableMixin, VListViewBase):
    """ Embedded view for rendering a list of related objects. """
    template_name = 'vprad/views/list/embedded_object_list.jinja.html'
    table_pagination = False
    table_base = EmbeddedTableBase
    object_limit = 15

    def get_queryset(self):
        qs = getattr(self.parent_object, self.parent_field_name).all()
        if self.object_limit:
            return qs[:self.object_limit]
        return qs

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['prefix'] = 'embed_filter_' + self.name
        return kwargs

    def create_url(self):
        local = self.get_local_field_name()
        try:
            return reverse(get_model_url_name(self.model, 'create')) + '?%s=%s' % (local,
                                                                                   self.parent_object.pk)
        except NoReverseMatch:
            return ''

    def moreinfo_url(self):
        local = self.get_local_field_name()
        try:
            return reverse(get_model_url_name(self.model, 'list')) + '?%s=%s' % (local,
                                                                                 self.parent_object.pk)
        except NoReverseMatch as e:
            return ''
