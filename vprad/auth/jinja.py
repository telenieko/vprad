from django.shortcuts import resolve_url

from vprad.auth import sign_url as _sign_url
from vprad.site.jinja import register_filter


@register_filter(name='urlsign')
def filter_urlsign(to,
                   expire_seconds=None,
                   *url_args, **url_kwargs):
    """ Return a signed URL. """
    resolved_url = resolve_url(to, *url_args, **url_kwargs)
    signed = _sign_url(resolved_url,
                       expire_seconds=expire_seconds)
    return signed.full_path()
