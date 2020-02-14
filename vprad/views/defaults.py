from django.contrib.auth import logout
from django.shortcuts import render
from django.views.generic import TemplateView

from vprad.views.registry import register_view


@register_view(name='home', urlpaths='')
def home(request):
    return TemplateView.as_view(template_name='vprad/home.jinja.html',
                                extra_context={'starred': {}})(request)


@register_view(urlpaths='login', name='login')
def login_view(request):
    raise NotImplementedError()


@register_view(urlpaths='logout', name='logout')
def logout_view(request):
    logout(request)
    return render(request, 'vprad/views/logout.jinja.html')
