import pytest
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView

from vprad.views.generic.mixin import ModelDataMixin


def test_model_data_mixin_get_model_or_object():
    class AListView(ModelDataMixin, ListView):
        model = get_user_model()

    class ADetailView(ModelDataMixin, DetailView):
        model = get_user_model()

    list = AListView()
    assert list._get_model_or_object() == get_user_model()
    detail = ADetailView()
    with pytest.raises(AttributeError):
        # .get_object() has not been called,
        # so .object should raise an AttributeError
        detail._get_model_or_object()


def test_get_headline_object(db):
    class ADetailView(ModelDataMixin, DetailView):
        model = get_user_model()

    object = get_user_model()()
    object.a_headline = 'a_headline'
    object.a_headline_callable = lambda: 'a_callable'
    view = ADetailView()

    view.object = object
    assert view.get_headline() == ''
    view.headline = 'a_headline'
    assert view.get_headline() == 'a_headline'
    view.headline = 'a_headline_callable'
    assert view.get_headline() == 'a_callable'


def test_get_headline_model(db):
    class AListView(ModelDataMixin, ListView):
        model = get_user_model()

    model = get_user_model()
    model.b_headline = 'b_headline'
    model.b_headline_callable = lambda: 'b_callable'
    view = AListView()

    assert view.get_headline() == 'user list'
    view.headline = 'b_headline'
    assert view.get_headline() == 'b_headline'
    view.headline = 'b_headline_callable'
    assert view.get_headline() == 'b_callable'
    del model.b_headline
    del model.b_headline_callable


def test_get_headline_subtitle(db):
    class ADetailView(ModelDataMixin, DetailView):
        model = get_user_model()

    object = get_user_model()()
    object.a_subtitle = 'a_subtitle'
    object.a_subtitle_callable = lambda: 'a_callable'
    view = ADetailView()

    view.object = object
    assert view.get_headline_subtitle() == '-'
    view.headline_subtitle = 'a_subtitle'
    assert view.get_headline_subtitle() == 'a_subtitle'
    view.headline_subtitle = 'a_subtitle_callable'
    assert view.get_headline_subtitle() == 'a_callable'

