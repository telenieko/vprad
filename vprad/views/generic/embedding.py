import logging
import typing as t

from django.db import models
from django.utils.decorators import classonlymethod
from django.views import View

logger = logging.getLogger('vprad.views')
# The parameter in GET for requesting an embeddable:
EMBEDDABLE_GET_PARAM = '_embed_related'


class VEmbeddableMixin:
    # Unique name for this embedable (within the same embedding view).
    # defaults to the name of the field.
    name: str = None
    # Name to show as the embed title
    verbose_name: str = None
    # Embedding object
    parent_object: models.Model = None  # The model instance from the embedding view.
    # The view that is calling us
    # TODO: Consider removing this.
    parent_view: View = None  # The embedding view instance
    # Our model.
    model: models.Model
    # Attribute of self.parent_object to get the embedded entity (ForeignKey)
    parent_attr: str = None
    # The field in this view's model to filter for equality with self.parent_object.pk
    # used in ManyToOne.
    filter_attr = None
    # Attribute in self.model that holds the relationship to the parent_object
    attr: str = None

    # noinspection PyUnresolvedReferences
    def dispatch(self, request, *args, **kwargs):
        if 'parent_object' in kwargs:
            self.parent_object = kwargs['parent_object']
        return super().dispatch(request, *args, **kwargs)

    @classmethod
    def create_embed_related_for_field(cls,
                                       embedding_name: str,
                                       model: t.Type[models.Model],
                                       field_name: str) -> t.Type['VEmbeddableMixin']:
        """ View factory for VEmbeddableMixin

        Create a subclass of VEmbedableMixin of the appropiate type
        based on the `field_name` field of the `model`.
        The new class name is based on the `field_name` and the `embedding_name`.
        """
        from vprad.views.generic.detail import VEmbeddableDetailView
        from vprad.views.generic.list import VEmbeddableListView

        embedding_name = embedding_name.rstrip('View')
        try:
            field = model._meta.get_field(field_name)
        except models.FieldDoesNotExist:
            field = model._meta.fields_map[field_name]
        attrs = {'name': field.name,
                 'model': field.related_model,
                 'parent_attr': field.name,
                 'filter_attr': field.field.name,
                 'attr': field.remote_field.name}
        class_name = embedding_name + "_%sEmbed" % field_name.title()
        if isinstance(field, models.ForeignKey):
            view_class = VEmbeddableDetailView
            attrs['verbose_name'] = field.verbose_name
        elif isinstance(field, models.OneToOneRel):
            view_class = VEmbeddableDetailView
            attrs['verbose_name'] = field.related_model._meta.verbose_name
        elif isinstance(field, models.ManyToOneRel):
            view_class = VEmbeddableListView
            attrs['verbose_name'] = field.related_model._meta.verbose_name_plural
            attrs['exclude'] = (field.field.name, )
        else:
            raise ValueError("Don't know how to create embeddable for field %s in %s" % (field_name, cls))
        return type(view_class)(class_name, (view_class,), attrs)

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
        for field in model._meta.fields:
            if isinstance(field, models.ForeignKey):
                # ForeignKeys are normally shown in the fields()
                # embed += (field.name,)
                pass
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
                view_class = i
                assert i.name, "You must define %s.name" % i
                assert i.verbose_name, "You must define %s.verbose_name" % i
                if hasattr(i, 'model'):
                    assert i.model, "You must define %s.model" % i
                if hasattr(i, 'filter_attr'):
                    assert i.filter_attr, "You must define %s.filter_attr" % i
            else:
                raise ValueError("Don't know how to make embed_related=%s work" % i)
            url = '?%s=%s' % (EMBEDDABLE_GET_PARAM, view_class.name)
            # noinspection PyUnresolvedReferences
            retval[view_class.name] = view_class.as_view()
        return retval

    def get_context_data(self, **kwargs):
        kwargs['embed_related'] = [e.view_class for e in self._embeddables.values()]
        return super().get_context_data(**kwargs)

