from vprad.auth import check_signature, SignedURL, jinja


def test_urlsign_filter_urlname():
    """ Test that the urlsign filter works with urls by name. """
    url = jinja.filter_urlsign('home')
    res = check_signature(url)
    assert url.startswith("/?")
    assert isinstance(res, SignedURL), "The url did not pass validation!"


def test_urlsign_filter_url():
    """ Test that the urlsign filter works with urls. """
    url = jinja.filter_urlsign('/')
    res = check_signature(url)
    assert isinstance(res, SignedURL), "The url did not pass validation!"
