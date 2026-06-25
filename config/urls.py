"""
URLs raíz del proyecto. Cada app pedagógica vive bajo su propio prefijo
(estilo "menú de módulos" tipo WinQSB).
"""
from django.contrib import admin
from django.urls import include, path

from apps.core import pwa

urlpatterns = [
    path("manifest.json", pwa.manifest, name="pwa_manifest"),
    path("service-worker.js", pwa.service_worker, name="pwa_service_worker"),
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("reemplazo-equipos/", include("apps.reemplazo_equipos.urls")),
    path("van-tir-payback/", include("apps.evaluacion_proyectos.urls")),
    path("flujo-de-caja/", include("apps.flujo_caja.urls")),
    path("tasa-de-descuento/", include("apps.tasa_descuento.urls")),
    path("analisis-de-riesgo/", include("apps.analisis_riesgo.urls")),
]
