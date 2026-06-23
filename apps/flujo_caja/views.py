from django.shortcuts import render

from apps.finance_engine import (
    depreciacion_lineal, depreciacion_acelerada_suma_digitos,
    calcular_van, interpretar_van, calcular_tir, interpretar_tir,
    calcular_payback, interpretar_payback, FinanceEngineError,
)
from .forms import FlujoCajaForm
from apps.core.graficos import svg_barras_con_linea


def _construir_tabla_flujo(datos):
    n = datos["horizonte_anios"]
    ingresos = datos["ingresos_anuales"]
    costos = datos["costos_anuales"]
    tasa_imp = datos["tasa_impuesto"]

    if datos["metodo_depreciacion"] == "lineal":
        dep = depreciacion_lineal(datos["inversion_inicial"], datos["valor_residual_contable"], n)
    else:
        dep = depreciacion_acelerada_suma_digitos(datos["inversion_inicial"], datos["valor_residual_contable"], n)

    filas = []
    flujo_neto = [-(datos["inversion_inicial"] + datos["capital_trabajo"])]  # año 0

    for t in range(n):
        ingreso = ingresos[t]
        costo = costos[t]
        depreciacion = dep.cuotas_anuales[t]
        utilidad_antes_imp = ingreso - costo - depreciacion
        impuesto = max(utilidad_antes_imp, 0) * tasa_imp  # impuesto solo si hay utilidad positiva
        utilidad_neta = utilidad_antes_imp - impuesto
        flujo_operacional = utilidad_neta + depreciacion  # se suma de vuelta: no es salida de caja

        flujo_periodo = flujo_operacional
        # En el último año: recuperar capital de trabajo y liquidar valor de salvamento (neto de impuesto)
        if t == n - 1:
            valor_libro_final = dep.valor_libro[-1]
            utilidad_venta_activo = datos["valor_residual_activos"] - valor_libro_final
            impuesto_venta = utilidad_venta_activo * tasa_imp  # puede ser negativo (ahorro) si hay pérdida contable
            flujo_periodo += datos["capital_trabajo"] + datos["valor_residual_activos"] - impuesto_venta

        flujo_neto.append(flujo_periodo)
        filas.append({
            "anio": t + 1,
            "ingreso": ingreso,
            "costo": costo,
            "depreciacion": depreciacion,
            "utilidad_antes_imp": utilidad_antes_imp,
            "impuesto": impuesto,
            "utilidad_neta": utilidad_neta,
            "flujo_periodo": flujo_periodo,
        })

    return filas, flujo_neto, dep


def inicio(request):
    form = FlujoCajaForm(request.POST or None)
    filas = flujo_neto = dep = None
    van = tir = payback = None
    error_calculo = None

    if request.method == "POST" and form.is_valid():
        try:
            filas, flujo_neto, dep = _construir_tabla_flujo(form.cleaned_data)
            tasa = form.cleaned_data["tasa_descuento"]
            van = interpretar_van(calcular_van(flujo_neto, tasa))
            tir = interpretar_tir(calcular_tir(flujo_neto), tasa_corte=tasa)
            tir.valor_pct = tir.valor * 100 if tir.valor is not None else None
            payback = interpretar_payback(calcular_payback(flujo_neto))
        except FinanceEngineError as exc:
            error_calculo = str(exc)
        except (IndexError, ZeroDivisionError) as exc:
            error_calculo = f"Error en los datos ingresados: {exc}"

    contexto = {
        "form": form,
        "filas": filas,
        "flujo_neto": flujo_neto,
        "dep": dep,
        "van": van, "tir": tir, "payback": payback,
        "error_calculo": error_calculo,
    }
    if flujo_neto:
        labels = [f"Año {i}" for i in range(len(flujo_neto))]
        contexto["svg_flujo"] = svg_barras_con_linea(labels, flujo_neto, payback.flujo_acumulado)

    return render(request, "flujo_caja/inicio.html", contexto)
