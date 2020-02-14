from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.urls import reverse

from vprad.views.registry import register_view


@register_view(urlpaths='login', name='login',
               replace='vprad.views.defaults.login_view')
def login_view(request):
    if 'username' in request.GET:
        username = request.GET['username']
        login(request,
              get_user_model().objects.get(username=username))
        if 'next' in request.GET:
            return redirect(request.GET['next'])
        return redirect('home')
    return render(request, 'login.jinja.html', {
        'users': get_user_model().objects.filter(is_active=True),
        'next': request.GET['next'] if 'next' in request.GET else 'home'})
