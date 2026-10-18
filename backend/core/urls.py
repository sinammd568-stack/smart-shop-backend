from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("", lambda request: JsonResponse({"service": "smart-shop-backend", "status": "ok"})),
    path("api/", include("chat.urls")),
]
