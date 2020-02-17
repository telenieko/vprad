from urllib.parse import urlparse

import pytest
from django.urls import reverse

from src.contacts.tests.factories import PersonFactory
from src.contacts.views import EmbeddedPhoneNumber, ContactDetailView
from vprad.views.generic.detail import VDetailView


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


def test_embedded_comes_from_registry(db):
    """ Test that if an embedded view is in the registry it is used. """
    view = ContactDetailView.as_view()
    embed = view.view_class._embeddables['phone_numbers'].view_class
    assert issubclass(embed, EmbeddedPhoneNumber)
