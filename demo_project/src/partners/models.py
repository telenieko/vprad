from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from model_utils.models import TimeStampedModel

from src.contacts.models import Contact


class Partner(TimeStampedModel):
    class PartnerStatus(models.IntegerChoices):
        NEW = 10, _('New account')
        APPROVED = 100, _('Approved partner')
        REJECTED = 200, _('Rejected partner')
        DISABLED = 201, _('Disabled partner')

    contact = models.OneToOneField(Contact,
                                   on_delete=models.PROTECT,
                                   null=False,
                                   unique=True,
                                   editable=False)
    status = models.IntegerField(choices=PartnerStatus.choices,
                                 default=PartnerStatus.NEW,
                                 editable=False,
                                 null=False,
                                 verbose_name=_('Partner status')
                                 )

    icon_class = 'industry'

    class Meta:
        verbose_name = _('Partner')
        verbose_name_plural = _('Partners')
