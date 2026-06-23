from django.urls import path

from . import views

app_name = "tasa_descuento"

urlpatterns = [
    path("", views.inicio, name="inicio"),
]
