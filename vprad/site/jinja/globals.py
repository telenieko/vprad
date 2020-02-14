from datetime import datetime, date

from django.contrib.messages import get_messages
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation

from vprad.helpers import get_icon_for
from .decorators import register_global

register_global(name='static')(static)
register_global(name='url')(reverse)
register_global(name='now')(datetime.now)
register_global(name='today')(date.today)

register_global(name='get_messages')(get_messages)
register_global(name='get_current_language')(translation.get_language)
register_global(name='get_icon_for')(get_icon_for)


@register_global(name='get_request_user')
def get_request_user(request):
    return request.user


@register_global(name='get_current_url')
def get_current_url(request):
    if 'ic-current-url' in request.GET:
        url = request.GET['ic-current-url']
        return url
    return request.path
