"""Vistas livianas para habilitar EvalProy como PWA instalable."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse


APP_VERSION = "evalproy-pwa-v1"


def manifest(request: HttpRequest) -> JsonResponse:
    """Entrega el Web App Manifest desde la raíz del sitio."""
    data = {
        "name": "EvalProy - Evaluación de Proyectos",
        "short_name": "EvalProy",
        "description": "Calculadora educativa para evaluación de proyectos: VAN, TIR, WACC, flujo de caja, reemplazo de equipos y análisis de riesgo.",
        "id": "/",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "display_override": ["standalone", "minimal-ui", "browser"],
        "orientation": "portrait-primary",
        "background_color": "#f8f9fb",
        "theme_color": "#1e3a8a",
        "categories": ["education", "productivity", "finance"],
        "lang": "es-CL",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-maskable-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
        "shortcuts": [
            {
                "name": "VAN/TIR",
                "short_name": "VAN/TIR",
                "description": "Evaluación de proyectos con VAN, TIR y payback.",
                "url": "/van-tir-payback/",
                "icons": [{"src": "/static/icons/icon-192.png", "sizes": "192x192"}],
            },
            {
                "name": "Flujo de Caja",
                "short_name": "Flujo",
                "description": "Construcción pedagógica de flujos de caja.",
                "url": "/flujo-de-caja/",
                "icons": [{"src": "/static/icons/icon-192.png", "sizes": "192x192"}],
            },
        ],
    }
    response = JsonResponse(data)
    response["Cache-Control"] = "public, max-age=3600"
    return response


def service_worker(request: HttpRequest) -> HttpResponse:
    """Entrega el service worker en /service-worker.js para cubrir todo el sitio."""
    script = f"""
const CACHE_NAME = "{APP_VERSION}";
const PRECACHE_URLS = [
  "/",
  "/manifest.json",
  "/static/css/evalproy.css",
  "/static/js/pwa-install.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png"
];

self.addEventListener("install", (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .catch(() => undefined)
  );
  self.skipWaiting();
}});

self.addEventListener("activate", (event) => {{
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
}});

self.addEventListener("fetch", (event) => {{
  const request = event.request;

  if (request.method !== "GET") {{
    return;
  }}

  const requestUrl = new URL(request.url);

  if (requestUrl.origin !== self.location.origin) {{
    return;
  }}

  if (request.mode === "navigate") {{
    event.respondWith(
      fetch(request).catch(() => caches.match("/"))
    );
    return;
  }}

  event.respondWith(
    caches.match(request).then((cachedResponse) => {{
      if (cachedResponse) {{
        return cachedResponse;
      }}

      return fetch(request).then((networkResponse) => {{
        if (!networkResponse || networkResponse.status !== 200) {{
          return networkResponse;
        }}

        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
        return networkResponse;
      }});
    }})
  );
}});
""".strip()
    response = HttpResponse(script, content_type="application/javascript; charset=utf-8")
    response["Cache-Control"] = "public, max-age=0, must-revalidate"
    return response
