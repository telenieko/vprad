import logging
import typing as t

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.decorators import classonlymethod
from django.views import View

from vprad.views.helpers import get_model_url_name
from vprad.views.registry import model_views_registry
from vprad.views.types import ViewType

logger = logging.getLogger('vprad.views')
# The parameter in GET for requesting an embeddable:
EMBEDDABLE_GET_PARAM = '_embed_related'


class VEmbeddableMixin:
    # Unique name for this embedable (within the same embedding view).
    # defaults to the name of the field.
    name: str = None
    verbose_name: str
    # Embedding object
    parent_object: models.Model = None # The model instance from the embedding view.
    # Our model.
    model: models.Model = None
    # The name of the field from which we were born,
    # we don't store the field directly as that conflicts when putting GenericRelation
    # on a class definition (fields do not appear to be fully ready at the time).
    parent_field_name: str = None

    def get_parent_field(self):
        return self.parent_object._meta.get_field(self.parent_field_name)

    def get_local_field_name(self):
        """ Get the local field name of the relation. """
        parent_field = self.get_parent_field()
        try:
            return parent_field.field.name
        except AttributeError:
            return parent_field.remote_field.name

    # noinspection PyUnresolvedReferences
    def dispatch(self, request, *args, **kwargs):
        if 'parent_object' in kwargs:
            self.parent_object = kwargs['parent_object']
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _get_verbose_name(field, plural: bool = False):
        try:
            return getattr(field, 'verbose_name')
        except AttributeError:
            if not plural:
                return field.related_model._meta.verbose_name
            return field.related_model._meta.verbose_name_plural

    @classmethod
    def create_embed_related_for_field(cls,
                                       embedding_name: str,
                                       embedding_model: t.Type[models.Model],
                                       field_name: str) -> t.Type['VEmbeddableMixin']:
        """ View factory for VEmbeddableMixin

        Create a subclass of VEmbedableMixin of the appropiate type
        based on the `field_name` field of the `model`.
        The new class name is based on the `field_name` and the `embedding_name`.
        """
        from vprad.views.generic.detail import VEmbeddableDetailView
        from vprad.views.generic.list import VEmbeddableListView

        try:
            field = embedding_model._meta.get_field(field_name)
        except models.FieldDoesNotExist:
            field = embedding_model._meta.fields_map[field_name]
        embedded_model = field.related_model
        attrs = {'name': field.name,
                 'model': field.related_model,
                 'parent_field_name': field.name}
        if hasattr(field, 'field'):
            attrs['exclude'] = (field.field.name,)
        elif hasattr(field, 'from_fields'):
            attrs['exclude'] = tuple(field.from_fields)
        class_name = embedding_name + "_%sEmbed" % field_name.title()
        if isinstance(field, (models.ForeignKey,
                              models.OneToOneRel)) or (isinstance(field, GenericRelation) and field.one_to_one):
            view_base = VEmbeddableDetailView
        elif isinstance(field, (models.ManyToOneRel,
                                GenericRelation)):
            view_base = VEmbeddableListView
        else:
            raise ValueError("Don't know how to create embeddable for field %s of type %s in %s" % (
                field_name, field.__class__, cls))
        view_type = ViewType.EMBED_DETAIL if issubclass(view_base, VEmbeddableDetailView) else ViewType.EMBED_LIST

        embedded_name = get_model_url_name(embedded_model, view_type)
        try:
            view_base = model_views_registry[embedded_name].view
        except KeyError:
            pass

        attrs['verbose_name'] = cls._get_verbose_name(field, view_type == ViewType.EMBED_LIST)
        return type(view_base)(class_name, (view_base,), attrs)

    def get_context_data(self, **kwargs):
        kwargs['embed'] = self
        return super().get_context_data(**kwargs)

    @classmethod
    def embed_url(cls):
        return '?%s=%s' % (EMBEDDABLE_GET_PARAM, cls.name)

    def create_url(self):
        raise NotImplementedError()

    def moreinfo_url(self):
        raise NotImplementedError()


class VEmbeddingMixin:
    """ Embedding of related items in a view. """
    model: t.Type[models.Model] = None  # Model of the Embedding view.
    embed_related: t.Tuple[t.Union[str, t.Type[VEmbeddableMixin]]] = None
    _embeddables: t.Dict[str, t.Callable] = None

    @classonlymethod
    def as_view(cls, **initkwargs):
        # noinspection PyUnresolvedReferences
        view = super().as_view(**initkwargs)
        logger.debug("Initialize '%s' for model '%s'", cls.__name__, cls.model)
        if not cls.model:
            raise ValueError("You must define `model` in a VEmbeddingMixin view")
        if not cls.embed_related:
            cls.embed_related = cls._embed_related_default(cls.model)
        cls._embeddables = cls._create_embed_related_views(cls.embed_related)
        return view

    # noinspection PyUnresolvedReferences
    def dispatch(self, request, *args, **kwargs):
        if EMBEDDABLE_GET_PARAM in request.GET:
            kwargs['parent_object'] = self.get_object()
            embeddable = self._embeddables[request.GET[EMBEDDABLE_GET_PARAM]]
            return embeddable(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    @classmethod
    def _embed_related_default(cls, model: t.Type[models.Model]):
        """ Produce a default for cls.embed_related """
        embed = tuple()
        for rel in model._meta.related_objects:
            if isinstance(rel, models.ManyToOneRel):
                embed += (rel.name,)
        return embed

    @classmethod
    def _create_embed_related_views(cls,
                                    embeddable: t.Tuple[t.Union[str, t.Type[VEmbeddableMixin]]]):
        """ Create the appropiate VEmbeddable** classes. """
        retval = {}
        for i in embeddable:
            if isinstance(i, str):
                view_class = VEmbeddableMixin.create_embed_related_for_field(cls.__name__, cls.model, i)
            elif issubclass(i, VEmbeddableMixin):
                assert i.name, "You must define %s.name" % i
                assert i.verbose_name, "You must define %s.verbose_name" % i
                assert i.model, "You must define %s.model" % i
                assert i.parent_field_name, "You must define %s.parent_field_name" % i
                view_class = i
            else:
                raise ValueError("Don't know how to make embed_related=%s work" % i)
            url = '?%s=%s' % (EMBEDDABLE_GET_PARAM, view_class.name)
            # noinspection PyUnresolvedReferences
            retval[view_class.name] = view_class.as_view()
        return retval

    def get_context_data(self, **kwargs):
        kwargs['embed_related'] = [e.view_class for e in self._embeddables.values()]
        return super().get_context_data(**kwargs)

