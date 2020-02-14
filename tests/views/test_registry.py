import types

from src.contacts.views import sample_view
from src.demo_project.views import login_view
from vprad.views.registry import views_registry, model_views_registry
from vprad.views.types import ViewItem, ModelViewItem


def test_func_views_registered():
    vi: ViewItem = views_registry['sample_view']
    assert vi.get_view_path() == 'src.contacts.views.sample_view'
    assert vi.get_view() == sample_view


def test_func_views_replaced():
    # We replace the login view on the demo_project
    # so we check if it got replaced.
    vi: ViewItem = views_registry['login']
    assert vi.get_view_path() == 'src.demo_project.views.login_view'
    assert vi.get_view() == login_view


def test_class_views_registered():
    contact_list_view: ModelViewItem = model_views_registry['contacts_contact_list']
    assert contact_list_view.get_view_path() == 'src.contacts.views.ContactListView'
    view_func = contact_list_view.get_view()
    assert isinstance(view_func, types.FunctionType)
