from typing import Any, Sequence

import factory
from factory import DjangoModelFactory, Faker, post_generation, SubFactory
from factory.fuzzy import FuzzyChoice

from src.contacts.models import Contact, ContactPostalAddress, ContactPhoneNumber, ContactEmailAddress
from src.users.tests.factories import UserFactory


class PostalAddressFactory(DjangoModelFactory):
    address_to = Faker('name')
    postal_code = Faker('postcode')
    country = Faker('country_code')

    @factory.post_generation
    def address_lines(self, create, extracted, **kwargs):
        address = Faker('address').generate({}).split('\n')
        self.address_line1 = address[0]
        self.address_line2 = address[1] if len(address) > 1 else None

    class Meta:
        model = ContactPostalAddress


class PhoneNumberFactory(DjangoModelFactory):
    number = Faker('phone_number')
    can_sms = FuzzyChoice([True, False])

    class Meta:
        model = ContactPhoneNumber


class EmailAddressFactory(DjangoModelFactory):
    email = Faker('email')

    class Meta:
        model = ContactEmailAddress


class ContactFactoryMixin(DjangoModelFactory):
    language = FuzzyChoice(Contact.Languages.values)
    web_address = Faker('url', schemes=['http', 'htttps'])
    assignee = SubFactory(UserFactory)

    addresses = factory.RelatedFactoryList(PostalAddressFactory,
                                           'parent',
                                           size=3)
    numbers = factory.RelatedFactoryList(PhoneNumberFactory,
                                         'parent',
                                         size=4)
    emails = factory.RelatedFactoryList(EmailAddressFactory,
                                        'parent',
                                        size=5)


class PersonFactory(ContactFactoryMixin):
    contact_type = Contact.ContactType.NATURAL
    first_name = Faker('first_name')
    last_name = Faker('last_name')

    class Meta:
        model = Contact


class CompanyFactory(ContactFactoryMixin, DjangoModelFactory):
    contact_type = Contact.ContactType.ENTITY
    first_name = Faker('company')

    class Meta:
        model = Contact

