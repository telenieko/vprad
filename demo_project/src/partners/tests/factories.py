from typing import Any, Sequence

import factory
from factory import DjangoModelFactory, Faker, post_generation, SubFactory
from factory.fuzzy import FuzzyChoice

from src.contacts.models import Contact, ContactPostalAddress, ContactPhoneNumber, ContactEmailAddress
from src.contacts.tests.factories import CompanyFactory
from src.partners.models import Partner
from src.users.tests.factories import UserFactory


class PartnerFactory(DjangoModelFactory):
    contact = SubFactory(CompanyFactory)
    status = FuzzyChoice(Partner.PartnerStatus.values)

    class Meta:
        model = Partner
