from urllib.parse import urlparse

import pytest
from django.urls import reverse

from src.contacts.tests.factories import PersonFactory


@pytest.mark.selenium
def test_contact_list_opens(live_server, authenticated_browser, db):
    PersonFactory.create_batch(40)
    browser = authenticated_browser
    browser.get(live_server.url + reverse('contacts_contact_list'))
    assert urlparse(browser.current_url).path == reverse('contacts_contact_list')


def test_contact_list_renders(user_client, db):
    PersonFactory.create_batch(40)
    resp = user_client.get(reverse('contacts_contact_list'))
    assert resp.status_code == 200


@pytest.mark.selenium
def test_contact_detail_opens(live_server, authenticated_browser, db):
    contact = PersonFactory.create_batch(40)[0]
    path = reverse('contacts_contact_detail', args=[contact.pk])
    authenticated_browser.get(live_server.url + path)
    assert urlparse(authenticated_browser.current_url).path == path


def test_contact_detail_renders(user_client, db):
    contact = PersonFactory.create_batch(40)[0]
    resp = user_client.get(reverse('contacts_contact_detail', args=[contact.pk, ]))
    assert resp.status_code == 200
