from django.urls import path

from . import views

app_name = "reemplazo_equipos"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("vida-economica/", views.vida_economica, name="vida_economica"),
    path("momento-optimo/", views.momento_optimo, name="momento_optimo"),
]
