from django.shortcuts import render

# Catálogo de módulos del sitio: una sola fuente de verdad para el menú
# de navegación y la portada (estilo "selector de módulos" de WinQSB).
MODULOS = [
    {
        "slug": "reemplazo-equipos",
        "nombre": "Reemplazo de Equipos",
        "descripcion": "Calcula la vida económica de un equipo y el momento óptimo de reemplazo frente a un desafiante, con el método del Costo Anual Equivalente (CAE).",
        "url_name": "reemplazo_equipos:inicio",
        "icono": "bi-arrow-repeat",
        "color": "tema-1",
    },
    {
        "slug": "van-tir-payback",
        "nombre": "VAN, TIR y Payback",
        "descripcion": "Evalúa proyectos ante certidumbre: VAN, TIR, Payback, tasa de Fisher e IVAN para rankear alternativas.",
        "url_name": "evaluacion_proyectos:inicio",
        "icono": "bi-graph-up-arrow",
        "color": "tema-2",
    },
    {
        "slug": "flujo-de-caja",
        "nombre": "Constructor de Flujo de Caja",
        "descripcion": "Construye paso a paso el flujo de caja de tu proyecto: inversión, ingresos, costos, depreciación, capital de trabajo e impuestos.",
        "url_name": "flujo_caja:inicio",
        "icono": "bi-cash-coin",
        "color": "tema-3",
    },
    {
        "slug": "tasa-de-descuento",
        "nombre": "Tasa de Descuento (WACC/CAPM)",
        "descripcion": "Calcula el costo del patrimonio (CAPM), el costo de la deuda y el WACC del proyecto, incluyendo ajuste de Beta.",
        "url_name": "tasa_descuento:inicio",
        "icono": "bi-percent",
        "color": "tema-4",
    },
    {
        "slug": "analisis-de-riesgo",
        "nombre": "Análisis de Riesgo",
        "descripcion": "Sensibiliza variables clave, compara escenarios, construye árboles de decisión y valora opciones reales.",
        "url_name": "analisis_riesgo:inicio",
        "icono": "bi-shuffle",
        "color": "tema-5",
    },
]


def inicio(request):
    return render(request, "core/inicio.html", {"modulos": MODULOS})


def acerca(request):
    return render(request, "core/acerca.html")
