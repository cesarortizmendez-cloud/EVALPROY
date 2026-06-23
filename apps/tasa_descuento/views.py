from django.shortcuts import render

from apps.finance_engine import (
    costo_patrimonio_capm, desapalancar_beta, apalancar_beta,
    calcular_wacc, FinanceEngineError,
)
from .forms import CAPMForm, BetaForm, WACCForm


def inicio(request):
    """
    Calculadora unificada de tasa de descuento: CAPM (Ke), apalancamiento
    de Beta, y WACC final, en una sola pantalla con tres bloques claramente
    diferenciados (se pueden usar de forma independiente).
    """
    capm_form = CAPMForm(request.POST if "calcular_capm" in request.POST else None, prefix="capm")
    beta_form = BetaForm(request.POST if "calcular_beta" in request.POST else None, prefix="beta")
    wacc_form = WACCForm(request.POST if "calcular_wacc" in request.POST else None, prefix="wacc")

    capm_resultado = beta_resultado = wacc_resultado = None
    error_calculo = None

    try:
        if "calcular_capm" in request.POST and capm_form.is_valid():
            d = capm_form.cleaned_data
            capm_resultado = costo_patrimonio_capm(d["tasa_libre_riesgo"], d["beta"], d["premio_riesgo_mercado"])
            capm_resultado.ke_pct = capm_resultado.ke * 100

        if "calcular_beta" in request.POST and beta_form.is_valid():
            d = beta_form.cleaned_data
            if d["accion"] == "desapalancar":
                valor = desapalancar_beta(d["beta_dado"], d["deuda"], d["patrimonio"], d["tasa_impuesto"])
                etiqueta = "Beta desapalancado (del activo)"
            else:
                valor = apalancar_beta(d["beta_dado"], d["deuda"], d["patrimonio"], d["tasa_impuesto"])
                etiqueta = "Beta apalancado (con deuda del proyecto)"
            beta_resultado = {"valor": valor, "etiqueta": etiqueta, "accion": d["accion"]}

        if "calcular_wacc" in request.POST and wacc_form.is_valid():
            d = wacc_form.cleaned_data
            wacc_resultado = calcular_wacc(d["ke"], d["kd"], d["valor_patrimonio"], d["valor_deuda"], d["tasa_impuesto"])
            wacc_resultado.wacc_pct = wacc_resultado.wacc * 100
    except FinanceEngineError as exc:
        error_calculo = str(exc)

    return render(request, "tasa_descuento/inicio.html", {
        "capm_form": capm_form, "beta_form": beta_form, "wacc_form": wacc_form,
        "capm_resultado": capm_resultado, "beta_resultado": beta_resultado, "wacc_resultado": wacc_resultado,
        "error_calculo": error_calculo,
    })
