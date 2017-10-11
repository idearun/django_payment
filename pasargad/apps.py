from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class Config(AppConfig):
    name = 'pasargad'
    label = 'pasargad'
    verbose_name = _(u'Pasargad')
