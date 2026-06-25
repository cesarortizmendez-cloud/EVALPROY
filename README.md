# EvalProy

Calculadora web abierta y gratuita de evaluación de proyectos de inversión
(reemplazo de equipos, VAN/TIR/Payback, flujo de caja, WACC/CAPM, análisis
de riesgo). Creado por **Dr. César Ortiz Méndez** — https://cv-cesarortiz.vercel.app

Sin base de datos de negocio, sin creación de usuarios: cada cálculo es
stateless (se resuelve en el momento del request), pensado para
desplegarse gratis en Vercel.

## 1. Requisitos
- Python 3.11+ instalado y en el PATH
- Git
- Cuenta en GitHub
- Cuenta en Vercel (login con GitHub)

## 2. Levantar el proyecto en local (Windows, cmd, dentro de VS Code)

Abre la carpeta del proyecto en VS Code, luego abre una terminal
(``Terminal > New Terminal``, asegúrate que sea **cmd** y no PowerShell
si prefieres seguir estos comandos tal cual) y ejecuta:

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
pip install pytest
```

Verifica que el motor financiero funciona corriendo los tests:

```cmd
python -m pytest apps\finance_engine\tests -v
```

Crea las tablas internas de Django (solo afecta auth/sessions/admin, NO
hay modelos de negocio que migrar):

```cmd
python manage.py migrate
```

Levanta el servidor de desarrollo:

```cmd
python manage.py runserver
```

Abre el navegador en **http://127.0.0.1:8000/**

## 3. Subir el proyecto a GitHub

Desde la misma terminal cmd, en la raíz del proyecto:

```cmd
git init
git add .
git commit -m "Primer commit: estructura base + finance_engine + dashboard"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/evalproy.git
git push -u origin main
```

(Reemplaza `TU_USUARIO` por tu usuario de GitHub; antes debes haber creado
el repositorio vacío en github.com).

Cada vez que avancemos en el desarrollo, el flujo será:

```cmd
git add .
git commit -m "Mensaje describiendo el avance"
git push
```

## 4. Desplegar en Vercel (gratis)

1. Entra a https://vercel.com y haz login con tu cuenta de GitHub.
2. "Add New..." → "Project" → selecciona el repositorio `evalproy`.
3. Vercel detectará `vercel.json` automáticamente (framework: Other / Python).
4. En "Environment Variables" agrega (recomendado para producción):
   - `DJANGO_SECRET_KEY` → una clave larga y aleatoria (puedes generarla con
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
   - `DJANGO_DEBUG` → `False`
   - `DJANGO_ALLOWED_HOSTS` → `*.vercel.app,tu-dominio-si-tienes.com`
5. Click "Deploy". Cada push a `main` en GitHub vuelve a desplegar
   automáticamente (CI/CD incluido gratis).

## 5. Estructura del proyecto

```
evalproy/
├── apps/
│   ├── core/                  # dashboard, navegación, "Acerca de"
│   ├── finance_engine/        # motor de cálculo puro (sin Django) — el corazón del sitio
│   ├── reemplazo_equipos/     # módulo: CAUE / reemplazo de equipos
│   ├── evaluacion_proyectos/  # módulo: VAN, TIR, Payback, Fisher, IVAN
│   ├── flujo_caja/            # módulo: constructor de flujo de caja
│   ├── tasa_descuento/        # módulo: CAPM, Beta, WACC
│   └── analisis_riesgo/       # módulo: sensibilidad, escenarios, árboles, opciones reales
├── config/                    # settings, urls, wsgi
├── api/index.py               # entrypoint serverless para Vercel
├── templates/base.html        # layout responsivo compartido
├── static/css/evalproy.css
├── vercel.json
├── requirements.txt
└── manage.py
```

## 6. Estado actual del desarrollo

- [x] Motor financiero (`finance_engine`) con VAN, TIR, Payback, Fisher, IVAN,
      depreciación, CAPM/WACC, sensibilidad, escenarios, árboles de decisión,
      opciones reales y CAUE — con tests.
- [x] Esqueleto Django + dashboard de módulos + layout responsivo + footer
      con autoría.
- [ ] Formularios e interfaz de cada módulo conectados al motor (en progreso,
      módulo por módulo).
- [ ] Despliegue inicial en Vercel.

## PWA instalable

El proyecto incluye soporte PWA para que EvalProy pueda instalarse como aplicación en Android, Windows, macOS, iPhone y iPad.

Rutas principales:

- `/manifest.json`
- `/service-worker.js`
- `/static/icons/icon-192.png`
- `/static/icons/icon-512.png`

En Android y Windows el botón **Instalar en mi equipo** dispara la ventana nativa de instalación. En iPhone/iPad se muestra una guía para usar **Compartir → Agregar a pantalla de inicio** desde Safari.
