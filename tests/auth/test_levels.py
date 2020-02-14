import pytest
from django.http import HttpResponse
from django.urls import path, include
from django.utils import timezone

from vprad.auth import require_auth_level, AuthLevel
from vprad.auth import sign_url


pytestmark = pytest.mark.django_db


# region: Setup views and urls
def dumb_view(request):
    """ Simple view that returns the access level and user_pk

    The user_pk is returned, or -1 if Anonymous.
    The access level, as interpreted by the AuthMiddleware is returned.
    """
    level = str(getattr(request, 'v_auth_level', None)).encode('utf-8')
    user = str(request.user.pk if request.user.is_authenticated else -1).encode('utf-8')
    return HttpResponse(level + b"/" + user)


@require_auth_level(AuthLevel.ANONYMOUS)
def anon_view(request):
    return dumb_view(request)


@require_auth_level(AuthLevel.IMPLIED)
def implied_view(request):
    return dumb_view(request)


@require_auth_level(AuthLevel.CACHED)
def cached_view(request):
    return dumb_view(request)


urlpatterns = [
    path("default", dumb_view, name="test_default"),
    path("anonymous", anon_view, name="test_anonymous"),
    path("implied", implied_view, name="test_implied"),
    path("cached", cached_view, name="test_cached"),
    path("login", dumb_view, name="login"),
    ]
# endregion


@pytest.mark.urls('tests.auth.test_levels')
def test_login_exempt(client):
    """ The login URL can be accessed anonymously. """
    resp = client.get("/login")
    assert resp.status_code == 200


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_can_reach_anonymous(client):
    resp = client.get("/anonymous")
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.ANONYMOUS).encode('utf-8') + b"/-1"


@pytest.mark.urls('tests.auth.test_levels')
def test_authenticated_can_reach_anonymous(user_client, test_user):
    """ An authenticated user can access an anonymous view. """
    resp = user_client.get("/anonymous")
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.CACHED).encode('utf-8') + b"/" + str(test_user.pk).encode('utf-8')


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_with_signed_url_becomes_implied(client):
    resp = client.get(sign_url("/anonymous").full_path())
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.IMPLIED).encode('utf-8') + b"/-1"


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_with_mangled_signature_stays_anonymous(client):
    surl = sign_url("/anonymous").full_path() + "&mangled"
    resp = client.get(surl)
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.ANONYMOUS).encode('utf-8') + b"/-1"


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_with_expired_signature_stays_anonymous(client, mocker):
    m = mocker.patch('vprad.auth.urlsign._get_current_timestamp')
    m.return_value = int(timezone.now().timestamp())
    surl = sign_url("/anonymous", expire_seconds=10).full_path()
    m.return_value += 20
    resp = client.get(surl)
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.ANONYMOUS).encode('utf-8') + b"/-1"


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_cant_reach_implied(client):
    """ Anonymous cannot access an implied view. """
    resp = client.get("/implied")
    assert resp.status_code == 302


@pytest.mark.urls('tests.auth.test_levels')
def test_authenticated_can_reach_implied(user_client, test_user):
    resp = user_client.get("/implied")
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.CACHED).encode('utf-8') + b"/" + str(test_user.pk).encode('utf-8')


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_with_signature_can_reach_implied(client):
    resp = client.get(sign_url("/implied").full_path())
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.IMPLIED).encode('utf-8') + b"/-1"


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_with_expired_signature_cant_reach_implied(client, mocker):
    m = mocker.patch('vprad.auth.urlsign._get_current_timestamp')
    m.return_value = int(timezone.now().timestamp())
    url = sign_url("/implied", expire_seconds=10).full_path()
    m.return_value += 20
    resp = client.get(url)
    assert resp.status_code == 302


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_with_signature_becomes_its_user(client, test_user):
    url = sign_url("/implied", user_pk=test_user.pk).full_path()
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.IMPLIED).encode('utf-8') + b"/" + str(test_user.pk).encode('utf-8')


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_cant_reach_cached(client):
    resp = client.get("/cached")
    assert resp.status_code == 302


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_cant_reach_cached_even_with_signature(client):
    url = sign_url("/cached").full_path()
    resp = client.get(url)
    assert resp.status_code == 302


@pytest.mark.urls('tests.auth.test_levels')
def test_authenticated_can_reach_cached(user_client, test_user):
    resp = user_client.get("/cached")
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.CACHED).encode('utf-8') + b"/" + str(test_user.pk).encode('utf-8')


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_cant_reach_default(client):
    resp = client.get("/default")
    assert resp.status_code == 302


@pytest.mark.urls('tests.auth.test_levels')
def test_anonymous_cant_reach_default_not_even_signed(client):
    url = sign_url("/default").full_path()
    resp = client.get(url)
    assert resp.status_code == 302


@pytest.mark.urls('tests.auth.test_levels')
def test_authenticated_can_reach_default(user_client, test_user):
    resp = user_client.get("/default")
    assert resp.status_code == 200
    assert resp.content == str(AuthLevel.CACHED).encode('utf-8') + b"/" + str(test_user.pk).encode('utf-8')
