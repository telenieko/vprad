""" Authentication materials of vprad.

This module contains the following:
    - Tooling for doing URL signatures similar to GCS/S3 signed urls.
    - Login required middleware
    - AuthLevel

Signed URLs are very useful to allow anonymous access to resources. For example, a "Download your invoice"
for which we would allow an `AuthLevel.IMPLIED` from the URL we sent the user via e-mail or something.

They expire, if you want.

AuthLevel requirements can be set site-wide with the `MINIMUM_AUTH_LEVEL` settings,
or on a case-by-case basis with the `require_auth_level` decorator.
"""
import logging
import re
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _

from .types import AuthLevel, SignedUrlError, SignedURL
from .urlsign import sign_url, check_signature

logger = logging.getLogger(__name__)
AUTH_LEVEL_ATTR = '_auth_level_required'


class AuthMiddleware:
    """ Middleware to coordinate authentication.

        Any URL listed in settings.LOGIN_REQUIRED_URLS_EXCEPTIONS won't need auth.
        The 'login' url does not need authentication.
        Any URL other URL will have it's view wrapped with require_auth_level().

        The minimum auth level required is indicated in settings.MINIMUM_AUTH_LEVEL,
        defaults to `AuthLevel.CACHED` (the "standard").

        ------
        LOGIN_REQUIRED_URLS_EXCEPTIONS = (
            r'/topsecret/login(.*)$',
            r'/topsecret/logout(.*)$',
        )
        """
    _login_url = 'login'
    exceptions = tuple()

    @property
    def login_url(self):
        # We cannot use LOGIN_URL because it defaults to an URL outside
        # the VPRAD site.
        return resolve_url(getattr(settings, 'VPRAD_LOGIN_URL', self._login_url))

    def __init__(self, get_response):
        self.get_response = get_response
        self.exceptions = tuple(re.compile(url) for url in getattr(settings, 'LOGIN_REQUIRED_URLS_EXCEPTIONS', tuple()))
        self.exceptions += (re.compile(self.login_url), )

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        error_message = None
        request_level = AuthLevel.ANONYMOUS

        if request.user.is_authenticated:
            request_level = AuthLevel.CACHED
        elif request.GET and 'X-URL-Signature' in request.GET:
            result = check_signature(request.get_full_path())
            if isinstance(result, SignedURL):
                # TODO: CHECK result.verbs
                request_level = AuthLevel.IMPLIED
                if not request.user.is_authenticated and result.user_pk:
                    request.user = result.get_user()
            elif isinstance(result, SignedUrlError):
                if result == result.EXPIRED:
                    error_message = _('The URL has expired.')
                    request_level = AuthLevel.ANONYMOUS
                else:
                    error_message = _('The URL signature could not be validated.')
                    request_level = AuthLevel.ANONYMOUS
                    logger.warning("Signed url error (invalidated): %s", result)

        needed_level = getattr(settings, 'MINIMUM_AUTH_LEVEL', AuthLevel.CACHED)
        for url in self.exceptions:
            if url.match(request.path):
                needed_level = AuthLevel.ANONYMOUS
                break
        if hasattr(view_func, AUTH_LEVEL_ATTR):
            # noinspection PyProtectedMember
            needed_level = view_func._auth_level_required

        if request_level < needed_level:
            if error_message:
                messages.add_message(request, messages.WARNING, error_message)
            return self.get_login_redirect_response(request)

        request.v_auth_level = request_level
        return None

    def get_login_redirect_response(self, request, msg=None):
        path = request.build_absolute_uri()
        resolved_login_url = resolve_url(self.login_url)
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
                (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path, resolved_login_url)


def require_auth_level(level: AuthLevel):
    """
    Decorator to make sure a view is only reached with a minimum auth level.

        @require_auth_level(AuthLevel.CACHED)
        def my_view(request):
            # I can assume now that the user is decently authenticated
            ...
    """
    def _inner(func):
        setattr(func, AUTH_LEVEL_ATTR, level)
        return func
    return _inner


__all__ = [sign_url,
           check_signature,
           require_auth_level,
           SignedURL,
           SignedUrlError,
           AuthMiddleware]
