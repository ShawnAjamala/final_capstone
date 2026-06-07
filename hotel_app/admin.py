from django.contrib import admin

from django.contrib import admin
from .models import MpesaTransaction

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'amount', 'status', 'mpesa_receipt', 'created_at']
