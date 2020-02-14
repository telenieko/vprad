import os
from urllib.parse import urlparse

import pytest
from django.conf import settings

pytestmark = pytest.mark.selenium


def test_django_with_authenticated_user(live_server, authenticated_browser):
    browser = authenticated_browser
    browser.get(live_server.url)
    # Check I have not been sent to login!
    url = urlparse(browser.current_url)
    assert url.path == '/'


def _test_login_of_anonymous_user(live_server, selenium, test_user):
    browser = selenium
    browser.get(live_server.url)
    # I have been redirected!
    assert str(browser.current_url).endswith('/login?next=/')
    browser.find_element_by_xpath("//a[@class='socialaccount_provider google']")

    email_field = browser.find_element_by_name('login')
    email_field.send_keys(settings.TEST_USER_EMAIL)

    password_field = browser.find_element_by_name('password')
    password_field.send_keys(settings.TEST_USER_PASSWORD)

    # Click the 'login' button
    browser.find_element_by_css_selector(".primary").click()
    url = urlparse(browser.current_url)
    assert url.path == '/'


def _test_logout(live_server, authenticated_browser):
    browser = authenticated_browser
    browser.get(live_server.url)
    # Check I have not been sent to login!
    url = urlparse(browser.current_url)
    assert url.path == '/'
    browser.find_element_by_css_selector("#top_menu_logout").click()
    url = urlparse(browser.current_url)
    assert url.path == '/logout'
    # Click the 'logout' button
    # browser.find_element_by_css_selector(".primary").click()
    # url = urlparse(browser.current_url)
    # assert url.path == '/'



