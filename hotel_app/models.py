from django.db import models

class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ("Pending",   "Pending"),
        ("Completed", "Completed"),
        ("Failed",    "Failed"),
        ("Cancelled", "Cancelled"),
    ]

    checkout_request_id = models.CharField(max_length=100, unique=True)
    phone_number        = models.CharField(max_length=15)
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    reference           = models.CharField(max_length=100)
    description         = models.CharField(max_length=255, blank=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    mpesa_receipt       = models.CharField(max_length=50, blank=True, null=True)
    result_desc         = models.CharField(max_length=255, blank=True, null=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} | {self.amount} | {self.status}"

    class Meta:
        ordering = ["-created_at"]