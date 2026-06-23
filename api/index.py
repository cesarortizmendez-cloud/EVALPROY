"""
Punto de entrada para el despliegue serverless en Vercel.
Vercel detecta este archivo (Python) y lo expone como función serverless;
internamente delega todo el trabajo a la aplicación WSGI de Django.
"""
import os
import sys
from pathlib import Path

# Asegura que la raíz del proyecto esté en el path para poder importar 'config'
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
