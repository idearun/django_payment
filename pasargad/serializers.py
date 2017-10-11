import json
from datetime import datetime

import requests
import xmltodict
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .models import PaymentRecord
from .settings import settings

MINIMUM_PAYMENT_AMOUNT = 1000  # IRR
MAXIMUM_PAYMENT_AMOUNT = 99000000  # IRR


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class PaymentRecordSerializer(serializers.ModelSerializer):
    """
    Creates a payment record on user request for payment.
    """
    payer = UserSerializer(read_only=True)
    transaction_code = serializers.ReadOnlyField()

    class Meta:
        model = PaymentRecord
        fields = ['amount', 'payer', 'transaction_code']

    def validate_amount(self, amount):
        if amount < MINIMUM_PAYMENT_AMOUNT:
            raise serializers.ValidationError(
                _("You chan't pay less than {0} rials.").format(MINIMUM_PAYMENT_AMOUNT))
        if amount > MAXIMUM_PAYMENT_AMOUNT:
            raise serializers.ValidationError(
                _("You can't pay more than {0} rials.").format(MAXIMUM_PAYMENT_AMOUNT))
        return amount

    def create(self, validated_data):
        validated_data['payer'] = self.user
        return super(PaymentRecordSerializer, self).create(validated_data)


class PaymentProcessSerializer(serializers.ModelSerializer):
    """

    """
    payer = UserSerializer(read_only=True)

    class Meta:
        model = PaymentRecord
        fields = ['payer', 'transaction_code']

    def validate_transaction_code(self, transaction_code):
        try:
            self.payment_record = PaymentRecord.objects.get(transaction_code=transaction_code)
            return transaction_code
        except PaymentRecord.DoesNotExist:
            raise serializers.ValidationError(_("Invalid transaction code!"))

    def create(self, validated_data):
        return self.payment_record


class PasargadSerializer(serializers.Serializer):
    terminalCode = serializers.CharField()
    merchantCode = serializers.CharField()
    redirectAddress = serializers.CharField()
    amount = serializers.IntegerField(min_value=MINIMUM_PAYMENT_AMOUNT, max_value=MAXIMUM_PAYMENT_AMOUNT,
                                      help_text=_("Payment amount (Rials)."))
    action = serializers.CharField()
    invoiceNumber = serializers.CharField()
    invoiceDate = serializers.CharField()
    timeStamp = serializers.CharField()
    sign = serializers.CharField()

    def __init__(self, amount, transaction_code, **kwargs):
        data = kwargs.pop('data', {})

        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        data['terminalCode'] = settings.get('TERMINAL_CODE')
        data['merchantCode'] = settings.get('MERCHANT_CODE')
        data['redirectAddress'] = settings.get('PASARGAD_REDIRECT_URL')
        data['amount'] = amount
        data['action'] = '1003'
        data['invoiceNumber'] = transaction_code
        data['invoiceDate'] = str(now)
        data['timeStamp'] = str(now)

        sign_string = "#".join(
            [data['merchantCode'], data['terminalCode'],
             data['invoiceNumber'], str(now), str(data['amount']),
             data['redirectAddress'], data['action'], str(now)])

        sign_string = "#%s#" % sign_string

        sign_string = sign_string.encode('utf-8')

        sign = sign_data(settings.get('PRIVATE_KEY_ADDRESS'), sign_string).decode('ascii')

        data['sign'] = sign

        super().__init__(data=data, **kwargs)


class PasargadConfirmSerializer(serializers.Serializer):
    tref = serializers.CharField()

    def validate(self, attrs):
        tref = attrs.get('tref', None)

        validate_data = {'invoiceUID': tref}
        post_response = requests.post(url=settings.get('PASARGAD_CHECK_TRANSACTION'), data=validate_data)

        xml_dict = xmltodict.parse(post_response.content)
        json_string = json.dumps(xml_dict)
        json_response = json.loads(json_string)

        if not ('resultObj' in json_response and 'result' in json_response['resultObj']):
            raise serializers.ValidationError(_("Error in data!"))

        if json_response['resultObj']['result'] in [False, 'False']:
            raise serializers.ValidationError(_("Invalid code!"))

        transaction_code = json_response['resultObj']['invoiceNumber']
        try:
            payment_transaction = PaymentRecord.objects.get(transaction_code=transaction_code)
        except:
            raise serializers.ValidationError(_("Invalid payment request!"))

        payment_transaction.tref = tref
        payment_transaction.save()

        verify_data = {}

        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        payment_transaction.add_log("%s - Trying to verify payment" % str(now))

        verify_data['terminalCode'] = json_response['resultObj']['terminalCode']
        verify_data['merchantCode'] = json_response['resultObj']['merchantCode']
        verify_data['amount'] = json_response['resultObj']['amount']
        verify_data['invoiceNumber'] = transaction_code
        verify_data['invoiceDate'] = json_response['resultObj']['invoiceDate']
        verify_data['timeStamp'] = str(now)

        sign_string = "#".join(
            [verify_data['merchantCode'], verify_data['terminalCode'], verify_data['invoiceNumber'],
             verify_data['invoiceDate'], str(verify_data['amount']), str(now)])

        sign_string = "#%s#" % sign_string
        sign_string = sign_string.encode('utf-8')
        sign = sign_data(settings.get('PRIVATE_KEY_ADDRESS'), sign_string).decode('ascii')
        verify_data['sign'] = sign

        verify_post_response = requests.post(url=settings.get('PASARGAD_VERIFY_TRANSACTION'), data=verify_data)
        verify_xml_dict = xmltodict.parse(verify_post_response.content)
        verify_json_string = json.dumps(verify_xml_dict)
        verify_json_response = json.loads(verify_json_string)

        payment_transaction.log_text += "\n - Received verification data"

        if not ('actionResult' in verify_json_response and 'result' in verify_json_response['actionResult']):
            payment_transaction.log_text += "\n - Invalid verification data structure"
            payment_transaction.save()
            raise serializers.ValidationError(_("Error in data!"))

        if not verify_json_response['actionResult']['result'] in [True, 'True']:
            payment_transaction.log_text += "\n - Verification failed"
            payment_transaction.save()
            if 'resultMessage' in verify_json_response['actionResult']:
                raise serializers.ValidationError(verify_json_response['actionResult']['resultMessage'])
            else:
                raise serializers.ValidationError(_("Error in payment. Please call the support."))

        if payment_transaction.successful:
            raise serializers.ValidationError(_("Payment record already closed successfully."))

        payment_transaction.log_text += "\n - Successful transaction"
        payment_transaction.save()
        payment_transaction.set_payed()

        return attrs

    def create(self, validated_data):
        return validated_data


def sign_data(private_key_loc, data):
    '''
    param: private_key_loc Path to your private key
    param: package Data to be signed
    return: base64 encoded signature
    '''
    from Crypto.Hash import SHA1
    from base64 import b64encode
    key = open(private_key_loc, "r").read()
    rsakey = RSA.importKey(key)
    signer = PKCS1_v1_5.new(rsakey)
    digest = SHA1.new()
    # It's being assumed the data is base64 encoded, so it's decoded before updating the digest
    digest.update(data)

    sign = signer.sign(digest)

    return b64encode(sign)
