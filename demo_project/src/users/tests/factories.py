from typing import Any, Sequence

from django.contrib.auth import get_user_model
from factory import DjangoModelFactory, Faker, post_generation


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        self.set_password(str(self.username) + "1234")

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]
