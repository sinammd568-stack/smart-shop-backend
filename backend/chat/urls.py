from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("products/", views.products, name="products"),
]
