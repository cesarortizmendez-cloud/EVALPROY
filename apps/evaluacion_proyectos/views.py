from django.shortcuts import render

from apps.finance_engine import (
    calcular_van, interpretar_van,
    calcular_tir, interpretar_tir,
    calcular_payback, interpretar_payback,
    calcular_tasa_fisher, interpretar_tasa_fisher,
    calcular_ivan, interpretar_ivan,
    FinanceEngineError,
)
from .forms import (
    VanTirForm, ComparacionFisherForm,
    FilaNoPeriodicaFormSet, TasaNoPeriodicaForm,
)
from apps.core.graficos import svg_barras_con_linea, svg_multilinea
from apps.finance_engine import (
    calcular_van_no_periodico, interpretar_van_no_periodico,
    calcular_tir_no_periodico, interpretar_tir_no_periodico,
)


def inicio(request):
    """
    Calculadora principal: VAN, TIR, Payback e IVAN sobre un único flujo
    de caja. Es el módulo más usado, por eso vive en la portada del sitio.
    """
    form = VanTirForm(request.POST or None)
    resultados = None
    error_calculo = None

    if request.method == "POST" and form.is_valid():
        flujos = form.cleaned_data["flujos"]
        tasa = form.cleaned_data["tasa_descuento"]
        tasa_corte = form.cleaned_data["tasa_corte_tir"] or tasa
        periodo_max = form.cleaned_data["periodo_maximo_payback"]

        try:
            van = interpretar_van(calcular_van(flujos, tasa))
            tir = interpretar_tir(calcular_tir(flujos), tasa_corte=tasa_corte)
            tir.valor_pct = tir.valor * 100 if tir.valor is not None else None
            payback = interpretar_payback(calcular_payback(flujos), periodo_maximo_aceptable=periodo_max)

            ivan_valor = None
            ivan_interpretacion = None
            if flujos[0] != 0:
                ivan_data = interpretar_ivan(calcular_ivan(van.valor, flujos[0]))
                ivan_valor = ivan_data["valor"]
                ivan_interpretacion = ivan_data["interpretacion"]

            labels = [f"Año {i}" for i in range(len(flujos))]
            resultados = {
                "van": van,
                "tir": tir,
                "payback": payback,
                "ivan_valor": ivan_valor,
                "ivan_interpretacion": ivan_interpretacion,
                "flujos": flujos,
                "tasa": tasa,
                "svg_flujo": svg_barras_con_linea(labels, flujos, payback.flujo_acumulado),
            }
        except FinanceEngineError as exc:
            error_calculo = str(exc)

    return render(request, "evaluacion_proyectos/inicio.html", {
        "form": form,
        "resultados": resultados,
        "error_calculo": error_calculo,
    })


def fisher(request):
    """
    Submódulo: tasa de Fisher para discriminar entre proyectos mutuamente
    excluyentes (cuándo conviene uno sobre el otro según la tasa de
    descuento que se use).
    """
    form = ComparacionFisherForm(request.POST or None)
    resultado = None
    error_calculo = None
    svg_fisher = None

    if request.method == "POST" and form.is_valid():
        a = form.cleaned_data["flujos_a"]
        b = form.cleaned_data["flujos_b"]
        nombre_a = form.cleaned_data["nombre_a"]
        nombre_b = form.cleaned_data["nombre_b"]

        try:
            fisher_resultado = interpretar_tasa_fisher(
                calcular_tasa_fisher(a, b), nombre_a=nombre_a, nombre_b=nombre_b
            )
            fisher_resultado.valor_pct = fisher_resultado.valor * 100 if fisher_resultado.valor is not None else None
            # Curva de VAN vs tasa para ambos proyectos (0% a 50%), para graficar el cruce
            tasas = [i / 100 for i in range(0, 51, 2)]
            van_a_serie = [calcular_van(a, t).valor for t in tasas]
            van_b_serie = [calcular_van(b, t).valor for t in tasas]
            tasas_grafico = [f"{t*100:.0f}%" for t in tasas]
            resultado = fisher_resultado
            svg_fisher = svg_multilinea(
                tasas_grafico,
                [
                    {"nombre": nombre_a, "valores": van_a_serie, "color": "#2563eb"},
                    {"nombre": nombre_b, "valores": van_b_serie, "color": "#dc2626"},
                ],
                titulo_x="Tasa de descuento",
            )
        except FinanceEngineError as exc:
            error_calculo = str(exc)

    return render(request, "evaluacion_proyectos/fisher.html", {
        "form": form,
        "resultado": resultado,
        "error_calculo": error_calculo,
        "svg_fisher": svg_fisher,
        "nombre_a": form.data.get("nombre_a", "Proyecto A"),
        "nombre_b": form.data.get("nombre_b", "Proyecto B"),
    })


def no_periodico(request):
    """
    Calculadora de VAN.NO.PER / TIR.NO.PER: para proyectos cuyos flujos NO
    ocurren en años exactos y consecutivos (ej. flujos en los años 2, 4 y 5,
    o fechas irregulares). Replica exactamente las funciones de Excel
    VAN.NO.PER y TIR.NO.PER, usando fechas reales y base de 365 días.
    """
    formset = FilaNoPeriodicaFormSet(request.POST or None, prefix="fila")
    tasa_form = TasaNoPeriodicaForm(request.POST or None, prefix="tasa")
    resultado_van = None
    resultado_tir = None
    error_calculo = None
    svg_flujo = None

    if request.method == "POST" and formset.is_valid() and tasa_form.is_valid():
        try:
            filas = [f.cleaned_data for f in formset if f.cleaned_data]
            filas.sort(key=lambda d: d["fecha"])
            fechas = [d["fecha"] for d in filas]
            flujos = [d["flujo"] for d in filas]

            tasa = tasa_form.cleaned_data["tasa_descuento"]
            tasa_corte = tasa_form.cleaned_data["tasa_corte_tir"] or tasa

            resultado_van = interpretar_van_no_periodico(calcular_van_no_periodico(fechas, flujos, tasa))
            resultado_tir = interpretar_tir_no_periodico(calcular_tir_no_periodico(fechas, flujos), tasa_corte=tasa_corte)
            if resultado_tir.valor is not None:
                resultado_tir.valor_pct = resultado_tir.valor * 100

            labels = [f.strftime("%d-%m-%Y") for f in fechas]
            acumulado = []
            suma = 0.0
            for f in flujos:
                suma += f
                acumulado.append(suma)
            svg_flujo = svg_barras_con_linea(labels, flujos, acumulado)
        except Exception as exc:  # noqa: BLE001 - mostramos cualquier error de datos al estudiante
            error_calculo = str(exc)

    return render(request, "evaluacion_proyectos/no_periodico.html", {
        "formset": formset,
        "tasa_form": tasa_form,
        "resultado_van": resultado_van,
        "resultado_tir": resultado_tir,
        "error_calculo": error_calculo,
        "svg_flujo": svg_flujo,
    })
