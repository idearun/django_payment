from django.conf.urls import url

from .views import PaymentRequestView, PaymentConfirmView, PaymentProcessView

urlpatterns = [
    url(r'^pasargad/request/$', PaymentRequestView.as_view()),
    url(r'^pasargad/process/$', PaymentProcessView.as_view()),
    url(r'^pasargad/confirm/$', PaymentConfirmView.as_view()),
]
