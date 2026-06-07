from django.urls import path, include
from django.shortcuts import render

def mpesa_test_page(request):
    return render(request, "mpesa_test.html")

urlpatterns = [
    path("", mpesa_test_page, name="mpesa_test"),          # ← serves the test page at /
    path("api/mpesa/", include("hotel_app.mpesa_urls")),
]