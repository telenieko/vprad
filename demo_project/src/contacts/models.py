from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel, SoftDeletableModel


class Contact(TimeStampedModel,
              SoftDeletableModel,
              models.Model):
    class ContactType(models.TextChoices):
        NATURAL = 'PF', _('Natural Person')
        ENTITY = 'PJ', _('Legal entity')

    class Languages(models.TextChoices):
        CATALAN = 'ca', _('Catalan')
        SPANISH = 'es', _('Spanish')
        ENGLISH = 'en', _('English')

    contact_type = models.CharField(max_length=2, choices=ContactType.choices,
                                    default=ContactType.NATURAL,
                                    null=False,
                                    blank=False,
                                    verbose_name=_('Type'))
    first_name = models.CharField(max_length=150, null=False, blank=False,
                                  help_text=_('First name, or legal name'),
                                  verbose_name=_('Name'))
    last_name = models.CharField(max_length=150, null=False, blank=True, default='',
                                 verbose_name=_('Last name'))
    full_name = models.CharField(max_length=300, null=False, blank=False, default='', editable=False,
                                 verbose_name=_('Full name'))

    assignee = models.ForeignKey(get_user_model(),
                                 null=True,
                                 editable=False,
                                 on_delete=models.PROTECT,
                                 related_name='assigned_contacts',
                                 verbose_name=_('Assigned to'),
                                 limit_choices_to={'is_active': True})
    language = models.CharField(max_length=2,
                                blank=False,
                                null=False,
                                verbose_name=_('Preferred language'),
                                choices=Languages.choices,
                                default=Languages.SPANISH)

    web_address = models.URLField(blank=True, null=False, default="",
                                  verbose_name=_('Página web'))

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        ordering = ('full_name',)

    icon_class = 'id badge'

    def __str__(self):
        # We don't use full_name, as that only gets updated on pre_save.
        return f"{self._calc_full_name()}"

    def _calc_full_name(self):
        if self.last_name and self.first_name:
            return '%s, %s' % (self.last_name, self.first_name)
        else:
            return self.last_name or self.first_name

    @staticmethod
    @receiver(pre_save)
    def _full_name(sender, instance, *, update_fields, **kwargs):
        if not isinstance(instance, Contact):
            return
        if update_fields is not None and 'first_name' not in update_fields and 'last_name' not in update_fields:
            return
        instance.full_name = instance._calc_full_name()


class ContactMechAbstract(TimeStampedModel):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True, null=False, verbose_name=_('Vigente'),
                                    help_text=_('Indica si el dato es vigente o no'))
    internal_note = models.TextField(null=False, blank=True, default='',
                                     verbose_name=_('Nota interna'))

    class Meta:
        abstract = True


class ContactPostalAddress(ContactMechAbstract):
    address_to = models.CharField(max_length=150, null=False, blank=True, default='',
                                  verbose_name=_('Address to'),
                                  help_text=_('To whom shall mailings be addresses'))
    address_line1 = models.CharField(max_length=150, null=False, blank=False,
                                     verbose_name=_('Address line'))
    address_line2 = models.CharField(max_length=150, null=False, blank=True, default='',
                                     verbose_name=_('Address line (extra)'))
    postal_code = models.CharField(max_length=10, null=False, blank=False,
                                   verbose_name=_('Postal code'))
    country = models.CharField(max_length=100, null=False, blank=True, default='',
                               verbose_name=_('Country'))

    class Meta:
        default_related_name = 'postal_addresses'
        verbose_name = _('Postal address')
        verbose_name_plural = _('Postal addresses')
        ordering = ('address_to', 'country')

    icon_class = 'address card'

    def __str__(self):
        s = self.address_to + '\n' if self.address_to != '' else ''
        s += self.address_line1 + '\n'
        s += self.address_line2 if self.address_line2 != '' else ''
        s += "%s, %s" % (self.postal_code, self.country)
        return s


class ContactPhoneNumber(ContactMechAbstract):
    # on a real app, you would go with PhoneNumberField.
    number = models.CharField(max_length=100, blank=False,
                              null=False, verbose_name=_('Number'))
    can_sms = models.BooleanField(default=False, null=False, verbose_name=_('Handles SMS'),
                                  help_text=_('Note if the number can receive SMS (if it can, not if it wants)'))

    class Meta:
        default_related_name = 'phone_numbers'
        verbose_name = _('Phone number')
        verbose_name_plural = _('Phone numbers')
        ordering = ('number',)

    icon_class = 'phone square'

    def __str__(self):
        return self.number


class ContactEmailAddress(ContactMechAbstract):
    email = models.EmailField(null=False, verbose_name=_('E-mail'))

    class Meta:
        default_related_name = 'email_addresses'
        ordering = ('email',)
        verbose_name = _('E-mail address')
        verbose_name_plural = _('E-mail addresses')

    icon_class = 'at'

    def __str__(self):
        return self.email
