from django import forms
from django.db.models import IntegerChoices
from django.utils.translation import gettext_lazy as _


class PartnerRejectform(forms.Form):
    class RejectReason(IntegerChoices):
        RISKY = 10, _('Too much risk')
        STARTUP = 20, _('Too young for risk assesment')

    reason = forms.ChoiceField(choices=RejectReason.choices,
                               required=True,
                               label=_('Reject reason'))
    may_reeval = forms.DateField(label=_('Re-evaluate risk on'),
                                 required=False)
