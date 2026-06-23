"""
Context processor global: inyecta nombre del sitio, tagline y autoría
en TODOS los templates sin tener que pasarlo manualmente en cada vista.
"""
from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "SITE_AUTHOR": settings.SITE_AUTHOR,
        "SITE_AUTHOR_URL": settings.SITE_AUTHOR_URL,
    }
