from django.contrib import admin

from .models import PaymentRecord


class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['payer_full_name', 'tref', 'transaction_code', 'amount', 'successful', 'created_at']
    list_filter = ['successful']
    date_hierarchy = 'created_at'
    readonly_fields = ['payer', 'amount', 'transaction_code', 'tref']
    search_fields = ['payer__username', 'tref', 'transaction_code']
    exclude = []

admin.site.register(PaymentRecord, PaymentRecordAdmin)
