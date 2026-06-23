from django.shortcuts import render

from apps.finance_engine import (
    calcular_van, FinanceEngineError,
    Escenario, analisis_escenarios,
    NodoDecision, evaluar_arbol_decision,
    opcion_real_black_scholes,
)
from .forms import (
    SensibilidadForm, EscenarioFormSet, EscenariosTasaForm,
    ArbolDecisionForm, OpcionRealForm,
)
from apps.core.graficos import svg_multilinea, svg_barras

VARIACIONES = (-0.20, -0.10, 0.0, 0.10, 0.20)


def inicio(request):
    """Portada del módulo: accesos directos a las 4 herramientas de riesgo."""
    return render(request, "analisis_riesgo/inicio.html")


def sensibilidad(request):
    """
    Sensibiliza los flujos futuros del proyecto (años 1 en adelante) en un
    rango de -20% a +20% y muestra cómo se mueve el VAN: el análisis de
    sensibilidad más simple y más usado en evaluación de proyectos.
    """
    form = SensibilidadForm(request.POST or None)
    puntos = None
    error_calculo = None

    if request.method == "POST" and form.is_valid():
        try:
            base = form.cleaned_data["flujos_base"]
            tasa = form.cleaned_data["tasa_descuento"]
            inversion = base[0]
            futuros = base[1:]

            puntos = []
            for variacion in VARIACIONES:
                nuevos_futuros = [f * (1 + variacion) for f in futuros]
                flujos = [inversion] + nuevos_futuros
                van = calcular_van(flujos, tasa).valor
                puntos.append({"variacion": variacion * 100, "van": van})

            van_base = next(p["van"] for p in puntos if p["variacion"] == 0)
            rango = max(p["van"] for p in puntos) - min(p["van"] for p in puntos)
        except FinanceEngineError as exc:
            error_calculo = str(exc)
            van_base = rango = None
    else:
        van_base = rango = None

    svg_sensibilidad = None
    if puntos:
        svg_sensibilidad = svg_multilinea(
            [f"{p['variacion']:+.0f}%" for p in puntos],
            [{"nombre": "VAN", "valores": [p["van"] for p in puntos], "color": "#dc2626"}],
            titulo_x="Variación de los flujos futuros",
        )

    return render(request, "analisis_riesgo/sensibilidad.html", {
        "form": form, "puntos": puntos, "van_base": van_base, "rango": rango,
        "error_calculo": error_calculo,
        "svg_sensibilidad": svg_sensibilidad,
    })


def escenarios(request):
    """Compara escenarios pesimista/base/optimista (o los que el usuario defina) con su probabilidad asociada."""
    formset = EscenarioFormSet(request.POST or None, prefix="esc")
    tasa_form = EscenariosTasaForm(request.POST or None, prefix="tasa")
    resultado = None
    error_calculo = None

    if request.method == "POST" and formset.is_valid() and tasa_form.is_valid():
        try:
            escenarios_obj = []
            for f in formset:
                d = f.cleaned_data
                if not d:
                    continue
                escenarios_obj.append(Escenario(nombre=d["nombre"], probabilidad=d["probabilidad"], flujos=d["flujos"]))
            tasa = tasa_form.cleaned_data["tasa_descuento"]
            resultado = analisis_escenarios(escenarios_obj, tasa)
        except FinanceEngineError as exc:
            error_calculo = str(exc)

    svg_escenarios = None
    if resultado:
        svg_escenarios = svg_barras(list(resultado.vanes.keys()), list(resultado.vanes.values()))

    return render(request, "analisis_riesgo/escenarios.html", {
        "formset": formset, "tasa_form": tasa_form, "resultado": resultado,
        "error_calculo": error_calculo,
        "svg_escenarios": svg_escenarios,
    })


def arbol_decision(request):
    """Árbol de decisión simplificado de 2 niveles: Invertir vs No Invertir, con nodo de azar éxito/fracaso."""
    form = ArbolDecisionForm(request.POST or None)
    resultado = None

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        nodo_azar = NodoDecision(
            nombre="Resultado de invertir", es_decision=False,
            hijos=[
                (None, d["prob_exito"], d["flujo_exito"]),
                (None, 1 - d["prob_exito"], d["flujo_fracaso"]),
            ],
        )
        raiz = NodoDecision(
            nombre="Decisión inicial", es_decision=True,
            hijos=[
                (nodo_azar, None, -d["costo_invertir"]),
                (None, None, d["flujo_no_invertir"]),
            ],
        )
        valor = evaluar_arbol_decision(raiz)
        valor_invertir = nodo_azar.valor_calculado - d["costo_invertir"]
        valor_no_invertir = d["flujo_no_invertir"]
        mejor = "Invertir" if valor_invertir >= valor_no_invertir else "No invertir"

        resultado = {
            "valor_esperado_azar": nodo_azar.valor_calculado,
            "valor_invertir": valor_invertir,
            "valor_no_invertir": valor_no_invertir,
            "mejor_decision": mejor,
            "interpretacion": (
                f"El valor esperado de invertir (descontando el costo de la inversión) es "
                f"${valor_invertir:,.0f}, comparado con ${valor_no_invertir:,.0f} de no invertir. "
                f"Aplicando 'rollback' (resolviendo el árbol de atrás hacia adelante), la decisión "
                f"óptima es: {mejor}."
            ),
        }

    return render(request, "analisis_riesgo/arbol_decision.html", {"form": form, "resultado": resultado})


def opciones_reales(request):
    """Valora la flexibilidad de esperar/expandir un proyecto usando Black-Scholes."""
    form = OpcionRealForm(request.POST or None)
    resultado = None
    error_calculo = None

    if request.method == "POST" and form.is_valid():
        try:
            d = form.cleaned_data
            resultado = opcion_real_black_scholes(
                valor_activo_subyacente=d["valor_activo"],
                precio_ejercicio=d["precio_ejercicio"],
                tasa_libre_riesgo=d["tasa_libre_riesgo"],
                volatilidad=d["volatilidad"],
                tiempo_anos=d["tiempo_anos"],
            )
        except FinanceEngineError as exc:
            error_calculo = str(exc)

    return render(request, "analisis_riesgo/opciones_reales.html", {
        "form": form, "resultado": resultado, "error_calculo": error_calculo,
    })
