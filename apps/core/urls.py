from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("acerca/", views.acerca, name="acerca"),
]
