import enum
from enum import Enum, auto
from typing import List, Optional

import attr
from django.contrib.auth import get_user_model


class AuthLevel(enum.IntEnum):
    """ Inform how much do we trust user identity.

    - `AuthLevel.ANONYMOUS`: There is no authentication at all.
    - `AuthLevel.IMPLIED`: The authentication is implied because the user
        came in with a signed url. The user can still be anonymous, but
        granted access to the view because of the valid signed url.
        (see, `require_auth_level` decorator).
    - `AuthLevel.CACHED`: The user is authenticated by Django, likely
        because of a session cookie. We say cached because the authentication
        itself might have happened on an earlier browser session.
    - `AuthLevel.GOOD`: Same as CACHED, but the authentication happened
        in the current browser session.

    The "normal" and sensible default is `AuthLevel.CACHED` as you would
    expect and is the equivalent of @login_required or any normal website.

    Note that `AuthLevel.GOOD` IS NOT YET IMPLEMENTED.
    """
    ANONYMOUS = enum.auto()
    IMPLIED = enum.auto()
    CACHED = enum.auto()
    GOOD = enum.auto()


class SignedUrlError(Enum):
    """ Informs about why `check_signature` failed. """
    INVALID_DATA = auto()
    EXPIRED = auto()
    MANGLED_DATA = auto()
    INVALID_SIGNATURE = auto()


@attr.s(slots=True, auto_attribs=True, init=True)
class SignedURL:
    """ A SignedURL object.

    You get it by calling `sign_url`, then you can call
    the `full_url` method to get a usable value for the user.
    You also get it by calling `check_signature` on a valid
    url.
    """
    path: str
    valid_until: int
    verbs: List[str]
    user_pk: Optional[int]
    signature: str

    def full_path(self):
        """ return full path to the SignedUrl. """
        u = self.path
        if '?' in u:
            u += '&'
        else:
            u += '?'
        u += "X-URL-Signature=" + self.signature
        return u

    def full_url(self, request):
        """ Return a full URL to the SignedURL

        We use the passed in request object to get the hostname and schema (http|https).
        """
        return request.build_absolute_uri(self.full_path())

    def get_user(self):
        """ If the signature payload had a `user_pk`, get the User. """
        if not self.user_pk:
            return None
        return get_user_model().objects.get(pk=self.user_pk)