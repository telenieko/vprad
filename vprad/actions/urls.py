from django.urls import path

from vprad.actions import actions_registry
from vprad.actions.views import ActionView

from vprad.helpers import LazyClosureSequence


def get_urls():
    """ Return urlpatters for the actions registered.
        action/<action_name>
        action/<action_name>/<pk>
    """
    urlpatterns = []
    for act in actions_registry.by_name.values():
        urlpath = act.full_name
        if act.needs_instance:
            urlpath += "/<str:pk>"
        urlpatterns.append(
            path(urlpath,
                 ActionView.as_view(action=act),
                 name=act.full_name)
        )
    return urlpatterns


urlpatterns = LazyClosureSequence(get_urls)
