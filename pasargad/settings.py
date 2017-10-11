from copy import deepcopy

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def merge_settings_dicts(a, b, path=None, overwrite_conflicts=True):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_settings_dicts(a[key], b[key], path + [str(key)], overwrite_conflicts=overwrite_conflicts)
            elif a[key] == b[key]:
                pass
            else:
                if overwrite_conflicts:
                    a[key] = b[key]
                else:
                    conflict_path = '.'.join(path + [str(key)])
                    raise Exception('Conflict at %s' % conflict_path)
        else:
            a[key] = b[key]
    return a


default_settings = {
    'PASARGAD_REQUEST_TRANSACTION': "https://pep.shaparak.ir/gateway.aspx",
    'PASARGAD_CHECK_TRANSACTION': "https://pep.shaparak.ir/CheckTransactionResult.aspx",
    'PASARGAD_VERIFY_TRANSACTION': "https://pep.shaparak.ir/VerifyPayment.aspx",
}

settings = merge_settings_dicts(
    deepcopy(default_settings), getattr(settings, 'PAYMENT', {}))


def get(key, raise_exception=True):
    try:
        return settings[key]
    except KeyError:
        raise ImproperlyConfigured('Missing settings: PAYMENT[\'{}\']'.format(key))

