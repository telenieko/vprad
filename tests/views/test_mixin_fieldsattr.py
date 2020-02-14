from django.contrib.auth import get_user_model

from vprad.views.generic.mixin import FieldsAttrMixin


def test_default_fields():
    User = get_user_model()

    class AClass(FieldsAttrMixin):
        model = User

    fields = AClass().fields
    assert 'id' in fields
    assert 'username' in fields


def test_include_fields():
    User = get_user_model()

    class AClass(FieldsAttrMixin):
        model = User
        include = ('first_name', 'date_joined')

    fields = AClass().fields
    assert fields == ('first_name', 'date_joined')


def test_exclude_fields():
    User = get_user_model()

    class AClass(FieldsAttrMixin):
        model = User
        exclude = ('password', )
    fields = AClass().fields
    assert 'password' not in fields
