# Instalación PWA de EvalProy

EvalProy quedó configurada como aplicación web progresiva (PWA), por lo que puede instalarse como acceso directo/app desde Android, Windows, macOS, iPhone y iPad.

## Archivos incorporados

- `apps/core/pwa.py`: sirve el `manifest.json` y el `service-worker.js` desde la raíz del sitio.
- `config/urls.py`: agrega las rutas `/manifest.json` y `/service-worker.js`.
- `templates/base.html`: conecta el manifest, íconos Apple/favicons, botón de instalación y script PWA.
- `static/js/pwa-install.js`: controla el botón “Instalar en mi equipo” y registra el service worker.
- `static/icons/`: contiene los íconos de instalación.
- `static/css/evalproy.css`: contiene el estilo de la tarjeta flotante de instalación.

## Comportamiento esperado

- En Android y Windows, el botón “Instalar en mi equipo” abre la ventana nativa de instalación cuando el navegador lo permite.
- En iPhone/iPad, se muestra la instrucción para abrir Safari, tocar Compartir y elegir “Agregar a pantalla de inicio”.
- Si la aplicación ya está instalada, la tarjeta no se muestra.

## Verificación después de desplegar

Revisar estas rutas en producción:

```txt
https://TU-DOMINIO/manifest.json
https://TU-DOMINIO/service-worker.js
https://TU-DOMINIO/static/icons/icon-192.png
```

También se puede revisar la instalación desde Chrome/Edge usando DevTools → Application → Manifest.
