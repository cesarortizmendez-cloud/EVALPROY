from django.urls import path

from . import views

app_name = "evaluacion_proyectos"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("fisher/", views.fisher, name="fisher"),
    path("no-periodico/", views.no_periodico, name="no_periodico"),
]
