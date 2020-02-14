""" Generic Detail Views from VPRAD.

Detail views start by inheriting VDetailView which is
equivalent to django's DetailView.

On __init__ (which happens once, when creating the URLconf)
the DetailView will create "embedded" views for relationships.
"""
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.views.generic import DetailView

from vprad.helpers import get_url_for
from vprad.views.generic.embedding import VEmbeddableMixin, VEmbeddingMixin
from vprad.views.generic.mixin import FieldsAttrMixin, ModelDataMixin
from vprad.views.helpers import get_model_url_name

logger = logging.getLogger(__name__)


class VDetailViewBase(FieldsAttrMixin,
                      ModelDataMixin,
                      DetailView):
    context_object_name = 'object'
    template_name = 'vprad/views/detail/object_detail.jinja.html'

    def get_context_data(self, **kwargs):
        kwargs['headline'] = self.get_headline()
        kwargs['headline_subtitle'] = self.get_headline_subtitle()
        kwargs['fields'] = self.fields
        kwargs['default_fields'] = self.default_fields
        return super().get_context_data(**kwargs)


class VEmbeddableDetailView(VEmbeddableMixin, VDetailViewBase):
    """ Embedded view for rendering OneToOne or ForeignKey. """
    template_name = 'vprad/views/detail/embedded_object_detail.jinja.html'

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            return render(request,
                          'vprad/views/detail/embedded_object_noexist.jinja.html',
                          context={'verbose_name': self.model._meta.verbose_name,
                                   'model': self.model,
                                   'create_url': self.create_url()})

    def get_object(self, queryset=None):
        try:
            return getattr(self.parent_object, self.parent_attr)
        except ObjectDoesNotExist:
            raise Http404

    def create_url(self):
        # TODO: urlencode
        next_url = self.request.path
        try:
            url = reverse(get_model_url_name(self.model, 'create'))
            return url + f"?_method-{self.attr}={self.parent_object.pk}&next={next_url}"
        except NoReverseMatch:
            return ''

    def moreinfo_url(self):
        return get_url_for(self.object) or ''


class VDetailView(VEmbeddingMixin, VDetailViewBase):
    """ An object Detail View.

    VPRAD's equivalent to Django's DetailView.
    """
    pass
