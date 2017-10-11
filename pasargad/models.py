import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PaymentRecord(models.Model):
    payer = models.ForeignKey(User, related_name='payment_records', verbose_name=_("Payer"))

    amount = models.BigIntegerField(default=0, verbose_name=_("Amount (IRR)"), help_text=_("Payment amount in IRR."))
    successful = models.BooleanField(default=False, verbose_name=_("Successful"))
    transaction_code = models.CharField(max_length=255, verbose_name=_("Transaction Code"), blank=True, null=True)
    tref = models.CharField(max_length=255, verbose_name=_("Bank Tref"), blank=True, null=True)

    # Todo: Athough it's a simple method to keep logs on a transaction, it maybe better to replace it with a simple log model
    log_text = models.TextField(default="", verbose_name=_("Log Text"),
                                help_text=_("Some logs as simple text, showing payment status."))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Payment Record")
        verbose_name_plural = _("Payment Records")

    def __str__(self):
        return " %s: %s" % (self.payer.get_full_name(), self.amount)

    def save(self, *args, **kwargs):
        # Creates a transaction code if it's empty. (normally, on object creation)
        if not self.transaction_code:
            self.transaction_code = ''.join(random.SystemRandom().choice(string.digits) for _ in range(10))

        super(PaymentRecord, self).save(*args, **kwargs)

    def set_payed(self):
        self.successful = True

        # Todo add balance to user profile, or change and order status, etc. (Whatever you wanna do with the payment)

        self.save()

    def add_log(self, log):
        self.log_text += "\n%s" % log
        self.save()

    def payer_full_name(self):
        return self.payer.get_full_name()

    payer_full_name.short_description = _("Payer")
