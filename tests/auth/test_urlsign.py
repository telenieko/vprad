import pytest
from django.utils import timezone

from vprad.auth import check_signature, sign_url, SignedURL, SignedUrlError


def test_no_signature_no_validation():
    result = check_signature("/some/url?name=joe")
    assert isinstance(result, SignedUrlError)
    assert result == SignedUrlError.INVALID_DATA


def test_mangled_url_fails():
    su = sign_url("/some/url?name=joe")
    # Bad data:
    result = check_signature(su.full_path() + "random_garbage")
    assert isinstance(result, SignedUrlError)
    assert result == SignedUrlError.INVALID_SIGNATURE
    # Mangled:
    result = check_signature(su.full_path() + "&another=parameter")
    assert isinstance(result, SignedUrlError)
    assert result == SignedUrlError.MANGLED_DATA
    # more Mangled:
    result = check_signature("/sub" + su.full_path())
    assert isinstance(result, SignedUrlError)
    assert result == SignedUrlError.MANGLED_DATA


def test_url_signer():
    secured_url = "/some/url"
    su = sign_url(secured_url)
    assert isinstance(su, SignedURL), "I expected a SignedURL"
    assert isinstance(check_signature(su.full_path()), SignedURL)

    querystring = "a=b&c=d"
    su = sign_url(secured_url + '?' + querystring)
    assert su.full_path().startswith(secured_url + "?" + querystring)
    assert isinstance(check_signature(su.full_path()), SignedURL)


def test_url_signer_user(test_user):
    secured_url = "/some/url"
    querystring = "a=b&c=d"

    su = sign_url(secured_url + '?' + querystring)
    assert su.get_user() is None
    su = sign_url(secured_url + '?' + querystring, user_pk=test_user.pk)
    assert su.get_user() == test_user
    assert isinstance(check_signature(su.full_path()), SignedURL)


def test_url_signer_expiry(mocker):
    m = mocker.patch('vprad.auth.urlsign._get_current_timestamp')
    m.return_value = int(timezone.now().timestamp())
    su = sign_url("/some/url", expire_seconds=10)
    m.return_value += 11
    result = check_signature(su.full_path())
    assert isinstance(result, SignedUrlError)
    assert result == SignedUrlError.EXPIRED


def test_url_signer_no_expiry(mocker):
    m = mocker.patch('vprad.auth.urlsign._get_current_timestamp')
    m.return_value = int(timezone.now().timestamp())
    su_noexpire = sign_url("/some/url", expire_seconds=-1)
    m.return_value += 10000
    assert su_noexpire.valid_until == -1
    assert isinstance(check_signature(su_noexpire.full_path()), SignedURL)


def test_urlsign_v1_expires(mocker, settings):
    # This tests fixed urls to keep around whenever we modify data structures
    # to make sure already sent out urls keep working.
    settings.DJANGO_SECRET_KEY = '279%knhhb)n65wceypq-x6%kihp=&1i%hc%f(ur8)cabqz^jhx'
    m = mocker.patch('vprad.auth.urlsign._get_current_timestamp')
    m.return_value = 1557065872

    # su = sign_url('/some/url?awesome=1&great=1000', expire_seconds=10)
    su = "/some/url?awesome=1&great=1000&X-URL-Signature=eyJwYXRoIjoiL3NvbWUvdXJsP2F3ZXNv" \
         "bWU9MSZncmVhdD0xMDAwIiwidmFsaWRfdW50aWwiOjE1NTcwNjU4ODIsInZlcmJzIjpudWxsLCJ1c2V" \
         "yX3BrIjpudWxsfQ:1j078B:qEm1VmZC-v3CNZhQ9ni5Pm3-crM"

    m.return_value += 5
    result = check_signature(su)
    assert isinstance(result, SignedURL), "The URL did not validate?? %s" % result

    m.return_value += 25
    result = check_signature(su)
    assert isinstance(result, SignedUrlError)
    assert result == SignedUrlError.EXPIRED


def test_urlsign_v1_no_expire(mocker, settings):
    # This tests fixed urls to keep around whenever we modify data structures
    # to make sure already sent out urls keep working.
    settings.DJANGO_SECRET_KEY = '279%knhhb)n65wceypq-x6%kihp=&1i%hc%f(ur8)cabqz^jhx'
    # su_noexpire = sign_url('/some/url?awesome=1&great=1000', expire_seconds=-1)
    su_noexpire = "/some/url?awesome=1&great=1000&X-URL-Signature=eyJwYXRoIjoiL3NvbWUvd" \
                  "XJsP2F3ZXNvbWU9MSZncmVhdD0xMDAwIiwidmFsaWRfdW50aWwiOi0xLCJ2ZXJicyI6b" \
                  "nVsbCwidXNlcl9wayI6bnVsbH0:1j078B:nbG_NHOeC485SVBI4rcY48rBIrE"
    result = check_signature(su_noexpire)
    assert isinstance(result, SignedURL), "The URL did not validate?? %s" % result


def test_full_url(rf):
    su = sign_url("/some/url")
    request = rf.get('/')
    full_url = su.full_url(request)
    assert full_url.startswith('http://testserver/some/url?X-URL-Signature=')
    with pytest.raises(ValueError,
                       match=r'check_signature\(\) expects a path, not an URL'):
        check_signature(full_url)
