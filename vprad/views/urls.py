import traceback

from django.urls import path

from vprad.actions import actions_registry
from vprad.actions.views import ActionView

from vprad.helpers import LazyClosureSequence
from vprad.views.helpers import get_model_url_path
from vprad.views.registry import views_registry, model_views_registry


def get_views_urls():
    """ Return urlpatters for the views registered.

    For _registered_views, the urls are just as passed to the register.
    For _model_views, the url is:
        <app_label>/<model_name>/<suffix>
        <app_label>/<model_name>/<pk>/<suffix>
    suffix being the rightmost part of the urlname if it has "_" in it,
    or the whole urlname otherwise.

    So, for a users.User, the url users_user_detail would be:
        /users/user/<pk>/detail
    """
    print("HELLO")
    urlpatterns = []
    for name, vi in views_registry.items():
        for p in vi.urlpaths:
            urlpatterns.append(
                path(p, vi.get_view(), name=vi.name)
            )
    for name, mvi in model_views_registry.items():
        action = mvi.name.split('_')[-1]
        urlpath = get_model_url_path(mvi.model,
                                     action,
                                     'id' if mvi.needs_instance else None)
        view = mvi.view
        urlpatterns.append(
            path(urlpath, mvi.get_view(), name=mvi.name)
        )
    return urlpatterns


urlpatterns = LazyClosureSequence(get_views_urls)
