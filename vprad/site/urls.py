from django.conf import settings
from django.urls import path, include

# TODO: How to autodiscover actions.urls and views.urls so there's no direct
#   coupling from here to there.


urlpatterns = [
    # TODO: See if we put this inside the site wrapper?
    path('select2/', include('django_select2.urls')),
    path('action/', include('vprad.actions.urls')),
    path('', include('vprad.views.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += path('__debug__/', include(debug_toolbar.urls)),
