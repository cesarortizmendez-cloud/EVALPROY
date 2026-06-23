from django.urls import path

from . import views

app_name = "analisis_riesgo"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("sensibilidad/", views.sensibilidad, name="sensibilidad"),
    path("escenarios/", views.escenarios, name="escenarios"),
    path("arbol-decision/", views.arbol_decision, name="arbol_decision"),
    path("opciones-reales/", views.opciones_reales, name="opciones_reales"),
]
