import django_filters
from braces.views import SelectRelatedMixin
from django.http import HttpResponse
from django_filters import FilterSet
import django_tables2 as tables

from src.contacts.models import Contact, ContactPostalAddress, ContactPhoneNumber
from vprad.views.generic.list import VListView, VEmbeddableListView
from vprad.views.generic.detail import VDetailView
from vprad.views.helpers import get_model_url_name
from vprad.views.registry import register_model_view, register_view


class ContactTable(tables.Table):
    pk = tables.LinkColumn(get_model_url_name(Contact, 'detail'),
                           args=[tables.A("pk")])
    # actions = ActionsColumn()
    # starred = StarColumn()

    class Meta:
        model = Contact
        attrs = {'class': 'ui celled compact table'}
        order_by = ('name', )
        fields = ('contact_type', 'full_name', 'language', 'assignee', )


class ContactFilter(FilterSet):
    full_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Contact
        fields = ['contact_type', 'full_name', 'assignee']


@register_model_view(model=Contact, action='list', needs_instance=False)
class ContactListView(SelectRelatedMixin,
                      VListView):
    table_class = ContactTable
    model = Contact
    select_related = ['assignee', ]
    filterset_class = ContactFilter


class PostalAddressTable(tables.Table):
    address = tables.Column(empty_values=())

    class Meta:
        model = ContactPostalAddress
        fields = ['address', ]
        show_header = False

    def render_address(self, record):
        return str(record)


class EmbeddedPostalAddress(VEmbeddableListView):
    name = 'postal_addresses'
    verbose_name = ContactPostalAddress._meta.verbose_name
    model = ContactPostalAddress
    table_class = PostalAddressTable
    filter_attr = 'contact'


class EmbeddedPhoneNumber(VEmbeddableListView):
    name = 'phone_numbers'
    verbose_name = ContactPhoneNumber._meta.verbose_name
    model = ContactPhoneNumber
    filter_attr = 'contact'
    include = ('number', )


@register_model_view(model=Contact, action='detail', needs_instance=True)
class ContactDetailView(SelectRelatedMixin,
                        VDetailView):
    model = Contact
    select_related = ['assignee', ]
    embed_related = ('partner',
                     EmbeddedPostalAddress,
                     EmbeddedPhoneNumber,
                     'email_addresses', )
    fields = (('full_name', 'contact_type'),
              ('assignee', 'language'),
              'web_address')


@register_view(name='sample_view', urlpaths='contacts/sample_view/')
def sample_view(request):
    return HttpResponse(b"Hello")


# TODO: Temporary to check hamburger link in embedded list
@register_model_view(model=ContactPostalAddress, action='list', needs_instance=False)
class PostalAddressListView(SelectRelatedMixin,
                            VListView):
    model = ContactPostalAddress