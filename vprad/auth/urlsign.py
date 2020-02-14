import logging
import re

from typing import Optional, List, Union
from urllib import parse
from django.core import signing
from django.core.signing import BadSignature
from django.utils import timezone

from vprad.auth import SignedUrlError, SignedURL

logger = logging.getLogger(__name__)


def _get_current_timestamp() -> int:
    """ Return current timestamp.

    This is put in a function to make it easier to mock on tests
    for testing expiry, etc.
    """
    return int(timezone.now().timestamp())


def sign_url(path: str, *,
             expire_seconds: int = None,
             verbs: List[str] = None,
             user_pk: Optional[int] = None
             ) -> SignedURL:
    """
    :param user_pk: PK of the user assumed by the URL
    :param expire_seconds: Lifespan of the URL in seconds from now. -1 = eternity.
    :param verbs: Valid HTTP Verbs as a list, defaults to ['GET', ]
    :param path: full path (without hostname or scheme)
    :return: SignedURL object
    """
    if expire_seconds is None:
        expire_seconds = 3600
    if expire_seconds >= 0:
        valid_until = _get_current_timestamp() + expire_seconds
    else:
        valid_until = -1
    payload = {
        'path': path,
        'valid_until': valid_until,
        'verbs': verbs,
        'user_pk': user_pk,
    }
    signature = signing.dumps(payload)
    return SignedURL(path=path, valid_until=valid_until, verbs=verbs,
                     user_pk=user_pk,
                     signature=signature)


def check_signature(path: str) -> Union[SignedUrlError, SignedURL]:
    """ Verify the signature of a URL.

    The URL should be absolute path (request.get_full_path())
    and include a X-URL-Signature querystring parameter.

    Returns True or False
    """
    if re.match(r'\w+://', path):
        raise ValueError("check_signature() expects a path, not an URL")
    parsed_url = parse.urlsplit(path)
    query_dict = parse.parse_qs(parsed_url.query)
    try:
        signature = query_dict['X-URL-Signature'][0]
    except (KeyError, ValueError):
        return SignedUrlError.INVALID_DATA

    try:
        payload = signing.loads(signature)
    except BadSignature:
        return SignedUrlError.INVALID_SIGNATURE

    valid_until = payload['valid_until']
    if 0 <= valid_until < _get_current_timestamp():
        return SignedUrlError.EXPIRED

    clean_url = re.sub(r"[?&]X-URL-Signature=[^&$]*", "", path)
    if payload['path'] != clean_url:
        return SignedUrlError.MANGLED_DATA

    return SignedURL(path=payload['path'],
                     valid_until=valid_until, verbs=payload['verbs'],
                     user_pk=payload['user_pk'],
                     signature=signature)
