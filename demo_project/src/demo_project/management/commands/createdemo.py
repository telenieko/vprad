from django.core.management.base import BaseCommand
from factory import SubFactory
from factory.fuzzy import FuzzyChoice

from src.contacts.tests.factories import PersonFactory, CompanyFactory
from src.partners.tests.factories import PartnerFactory
from src.users.tests.factories import UserFactory


class Command(BaseCommand):
    help = "Fill database with demo data."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        users = UserFactory.create_batch(5)
        partners = PartnerFactory.create_batch(10)
        entities = CompanyFactory.create_batch(20,
                                               assignee=FuzzyChoice(users))
        partners += PartnerFactory.create_batch(10, contact=SubFactory(PersonFactory))
        persons = PersonFactory.create_batch(20,
                                             assignee=FuzzyChoice(users))
