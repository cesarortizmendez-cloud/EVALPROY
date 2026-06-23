from django.urls import path

from . import views

app_name = "flujo_caja"

urlpatterns = [
    path("", views.inicio, name="inicio"),
]
