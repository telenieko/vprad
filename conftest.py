import pytest
from django.conf import settings
from django.test import RequestFactory
from pytest_django.lazy_django import skip_if_no_django

from src.users.tests.factories import UserFactory
from vprad.actions import actions_registry


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    # we make browser needing tests go last, so if we want to fail early,
    # it happens faster.
    browser_tests = []
    for item in items:
        # Tests that use selenium should go last.
        if {'authenticated_browser', 'selenium'}.intersection(item.fixturenames):
            browser_tests.append(item)
    for item in browser_tests:
        items.pop(items.index(item))
        items.append(item)


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('headless')
    chrome_options.add_argument("--window-size=1280x800")
    return chrome_options


@pytest.fixture
def selenium(selenium):
    selenium.maximize_window()
    return selenium


@pytest.fixture(autouse=True, scope="session")
def faker_default_locale():
    import factory
    factory.Faker.override_default_locale('es_ES')
    factory.Faker._DEFAULT_LOCALE = 'es_ES'


@pytest.fixture()
def test_user(db):
    user_ = UserFactory.create(username=settings.TEST_USER_USERNAME,
                               password=settings.TEST_USER_PASSWORD,
                               email=settings.TEST_USER_EMAIL)
    user_.set_password(settings.TEST_USER_PASSWORD)
    user_.save()
    return user_


@pytest.fixture()
def user_client(test_user):
    skip_if_no_django()
    from django.test.client import Client
    client = Client()
    client.login(username=settings.TEST_USER_USERNAME, password=settings.TEST_USER_PASSWORD)
    return client


@pytest.fixture()
def authenticated_browser(selenium, user_client, live_server):
    """Return a browser instance with logged-in user session."""
    cookie = user_client.cookies['sessionid']

    selenium.get(live_server.url)
    selenium.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
    selenium.implicitly_wait(3)
    selenium.refresh()

    return selenium


@pytest.fixture(scope='function')
def actions():
    """ Simple fixture to purge the actions registry. """
    yield
    actions_registry.by_name.clear()
