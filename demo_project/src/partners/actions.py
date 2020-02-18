from django import forms
from django.db import IntegrityError

from vprad.actions import ActionNotAllowed
from .forms import PartnerRejectform
from .models import Partner
from vprad.actions.decorators import transition, register_model_action
from django.utils.translation import gettext_lazy as _

from ..contacts.models import Contact


@register_model_action(model=Partner,
                       name='create',
                       verbose_name=_('Create new partner'),
                       takes_self=False)
def create_partner(request_user,
                   contact=forms.ModelChoiceField(queryset=Contact.objects.filter(partner__isnull=True),
                                                  widget=Contact.get_fk_widget())):
    return Partner.objects.create(contact=contact)


@transition(model=Partner,
            verbose_name=_('Approve partner account'),
            attached_field=Partner.status,
            source=[Partner.PartnerStatus.NEW,
                    Partner.PartnerStatus.REJECTED,
                    Partner.PartnerStatus.DISABLED],
            target=Partner.PartnerStatus.APPROVED,
            icon='thumbs up')
def approve_partner(instance, request_user):
    instance.save()


@transition(model=Partner,
            verbose_name=_('Reject partner account'),
            attached_field=Partner.status,
            source=[Partner.PartnerStatus.NEW,
                    Partner.PartnerStatus.APPROVED],
            target=Partner.PartnerStatus.REJECTED,
            icon='thumbs down')
def reject_partner(instance, request_user, why=PartnerRejectform):
    print(why.cleaned_data)
    instance.save()


@transition(model=Partner,
            verbose_name=_('Disable partner account'),
            attached_field=Partner.status,
            source=[Partner.PartnerStatus.NEW,
                    Partner.PartnerStatus.APPROVED,
                    Partner.PartnerStatus.REJECTED],
            target=Partner.PartnerStatus.DISABLED,
            icon='power off')
def disable_partner(instance, request_user,
                    reconsider=forms.BooleanField(label=_('Reconsider reenablement in  the future'),
                                                  initial=False)):
    print(reconsider)
    instance.save()
