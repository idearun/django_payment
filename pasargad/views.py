from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pasargad.api_helpers import ApiResponse
from .serializers import PaymentRecordSerializer, PaymentProcessSerializer, PasargadSerializer, \
    PasargadConfirmSerializer
from .settings import settings


class PaymentRequestView(generics.CreateAPIView):
    """
    Use this endpoint to create a payment request.
    Gives you a transaction code and a optionally a url to redirect the user to (for payment from mobile).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentRecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.user = request.user

        serializer.is_valid(raise_exception=True)
        payment_record = serializer.save()
        headers = self.get_success_headers(serializer.data)

        data = serializer.data

        # If in the settings, we've set to send user to a frontend side to redirect him to payment gateway
        # we should return the frontend url (along with the transaction code as get parameter) in response
        if settings.get('GIVE_PROCESS_URL', raise_exception=False):
            data['url'] = settings.get('PAYMENT_PROCESS_ADDRESS').format(payment_record.transaction_code)

        return Response(ApiResponse.get_base_response(response_code=status.HTTP_201_CREATED, data=data),
                        status=status.HTTP_201_CREATED, headers=headers)


class PaymentProcessView(generics.CreateAPIView):
    """
    Takes a transaction code, and returns the payment gateway data and url. The client app should post the data to the given url.
    """
    permission_classes = []
    serializer_class = PaymentProcessSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        payment_record = serializer.save()
        headers = self.get_success_headers(serializer.data)

        # Generate the payment data
        pasargad_data = {}
        pasargad_serializer = PasargadSerializer(payment_record.amount, payment_record.transaction_code)
        if pasargad_serializer.is_valid():
            pasargad_data = pasargad_serializer.data

        data = serializer.data
        # The gateway data, which we should post to the payment gateway
        data['pasargad'] = pasargad_data
        # The payment gateway address
        data['url'] = settings.get('PASARGAD_REQUEST_TRANSACTION')

        return Response(
            ApiResponse.get_base_response(data=data), headers=headers)


class PaymentConfirmView(generics.CreateAPIView):
    """
    Takes the tref code given by the bank (after payment is done), and finalizes the payment
    """
    permission_classes = []
    serializer_class = PasargadConfirmSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.user = request.user

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(ApiResponse.get_base_response(data=serializer.data), headers=headers)
