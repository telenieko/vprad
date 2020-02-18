from django_select2 import forms as ds2


class SearchFieldsMixin:
    """ Simple mixin to define fields for searching.

    Used by AutocompleteMixin.
    """
    @classmethod
    def get_search_fields(cls):
        raise NotImplementedError()


# noinspection PyMethodMayBeStatic
class AutocompleteMixin(SearchFieldsMixin):
    """ Simple mixin to automatically setup autocomplete widgets.
    """
    @classmethod
    def get_fk_widget(cls):
        """ Return the widget to use when selecting this model from a ForeignKey.

        ie. on a forms.ModelChoiceField. Example:
            return ds2.ModelSelect2Widget(search_fields=('name', ))
        """
        try:
            return ds2.ModelSelect2Widget(search_fields=cls.get_search_fields())
        except NotImplementedError:
            raise NotImplementedError("Implement either .get_search_fields or .get_fk_widget")

    @classmethod
    def get_multi_widget(cls):
        """ Return the widget to use when selecting multiple instances of the model.

        ie. a forms.ModelMultipleChoiceField.
        """
        try:
            return ds2.ModelSelect2MultipleWidget(search_fields=cls.get_search_fields())
        except NotImplementedError:
            raise NotImplementedError("Implement either .get_search_fields or .get_multi_widget")
