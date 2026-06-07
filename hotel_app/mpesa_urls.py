from django.urls import path
from hotel_app import views   # ← must be hotel_app.views, not just views

urlpatterns = [
    path("pay/",                              views.initiate_payment, name="mpesa_pay"),
    path("callback/",                         views.mpesa_callback,   name="mpesa_callback"),
    path("status/<str:checkout_request_id>/", views.payment_status,   name="mpesa_status"),
]