"""
Configuración de Django para evalproy.

Decisiones clave (ver arquitectura acordada):
- SIN base de datos de negocio: no hay modelos persistentes para los
  cálculos financieros (son stateless, se calculan en cada request).
- Django igual necesita un DATABASES mínimo para su propio funcionamiento
  interno (auth/sessions/admin tablas), así que usamos SQLite local SOLO
  para eso. En producción (Vercel) ni siquiera se migra: las sesiones se
  guardan en cookie firmada, no en DB.
- Sesiones en cookie firmada -> compatible con entornos serverless sin
  filesystem persistente (Vercel).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "clave-de-desarrollo-NO-usar-en-produccion-cambiar-via-variable-de-entorno",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "https://*.vercel.app"
).split(",")

# ---------------------------------------------------------------------------
# Apps instaladas
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # para formatear números en templates ($ y miles)
    # Apps propias
    "apps.core",
    "apps.finance_engine",  # no tiene modelos ni vistas, solo se incluye por consistencia
    "apps.reemplazo_equipos",
    "apps.evaluacion_proyectos",
    "apps.flujo_caja",
    "apps.tasa_descuento",
    "apps.analisis_riesgo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de datos: SOLO para tablas internas de Django (no se usa para
# guardar resultados financieros, que son siempre stateless / en sesión).
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_interno_django.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# Sesiones: cookie firmada, SIN tabla de base de datos.
# Clave para que funcione en serverless (Vercel) sin filesystem persistente.
# ---------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 60 * 60 * 4  # 4 horas: tiempo suficiente para un wizard de flujo de caja
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

AUTH_PASSWORD_VALIDATORS = []  # no hay creación de usuarios en este sitio

# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Archivos estáticos (servidos vía whitenoise, sin servidor externo)
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Datos del sitio / autoría (usados en context_processor para templates)
# ---------------------------------------------------------------------------
SITE_NAME = "EvalProy"
SITE_TAGLINE = "La calculadora universal de evaluación de proyectos de inversión"
SITE_AUTHOR = "Dr. César Ortiz Méndez"
SITE_AUTHOR_URL = "https://cv-cesarortiz.vercel.app"
