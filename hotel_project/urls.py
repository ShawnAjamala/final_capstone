
from django.contrib import admin
from django.urls import path, include
 
urlpatterns = [
    path("admin/",      admin.site.urls),
    path("",            include("hotel_app.urls")),     # your existing routes
    path("api/mpesa/",  include("hotel_app.mpesa_urls")),  # new M-Pesa routes
]
 