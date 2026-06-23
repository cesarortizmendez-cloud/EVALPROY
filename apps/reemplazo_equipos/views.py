import json

from django.shortcuts import render

from apps.finance_engine import (
    calcular_vida_economica, calcular_momento_optimo_reemplazo, FinanceEngineError,
)
from .forms import VidaEconomicaForm, MomentoOptimoForm
from .graficos import construir_svg_curva_cae, construir_svg_dos_series


def inicio(request):
    """Portada del módulo: las 2 calculadoras clásicas de reemplazo de equipos."""
    return render(request, "reemplazo_equipos/inicio.html")


def vida_economica(request):
    """
    Calculadora de Vida Económica por el método CAE: tantea n con la
    fórmula aproximada y confirma con el CAE exacto, igual que el ejercicio
    P1-P2 del Excel del curso y el ejemplo del apunte UNAB.
    """
    form = VidaEconomicaForm(request.POST or None)
    resultado = None
    error_calculo = None

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            rango = range(d["n_inicial_tanteo"], d["n_final_tanteo"] + 1)
            resultado = calcular_vida_economica(P=d["P"], A=d["A"], g=d["g"], i=d["i"], rango_tanteo=rango)
        except FinanceEngineError as exc:
            error_calculo = str(exc)
        except (OverflowError, ZeroDivisionError) as exc:
            error_calculo = f"Error numérico con estos datos: {exc}. Prueba con un rango de tanteo distinto."

    contexto = {"form": form, "resultado": resultado, "error_calculo": error_calculo}
    if resultado:
        contexto["labels_cae_json"] = json.dumps([f.n for f in resultado.tabla_cae])
        contexto["valores_cae_json"] = json.dumps([round(f.cae, 2) for f in resultado.tabla_cae])
        contexto["labels_tanteo_json"] = json.dumps([f.n_tanteado for f in resultado.tabla_tanteo])
        contexto["resultante_tanteo_json"] = json.dumps([round(f.n_resultante, 3) for f in resultado.tabla_tanteo])
        puntos = [(f.n, f.cae) for f in resultado.tabla_cae]
        contexto["svg_curva_cae"] = construir_svg_curva_cae(puntos, n_optimo=resultado.n_optimo)

    return render(request, "reemplazo_equipos/vida_economica.html", contexto)


def momento_optimo(request):
    """
    Calculadora de Momento Óptimo de Reemplazo: compara el CAE de la
    alternativa actual (que crece a una tasa conocida) contra el CAE
    constante del equipo/proceso desafiante, igual que los ejercicios P3
    y P4 del Excel del curso.
    """
    form = MomentoOptimoForm(request.POST or None)
    resultado = None
    error_calculo = None

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            resultado = calcular_momento_optimo_reemplazo(
                cae_desafiante=d["cae_desafiante"], cae_actual=d["cae_actual"], tasa_incremento=d["tasa_incremento"],
            )
        except FinanceEngineError as exc:
            error_calculo = str(exc)

    contexto = {"form": form, "resultado": resultado, "error_calculo": error_calculo}
    if resultado:
        anios = list(range(0, max(int(resultado.n_optimo) + 4, 6)))
        cae_actual_serie = [d["cae_actual"] * (1 + d["tasa_incremento"]) ** a for a in anios]
        cae_desafiante_serie = [d["cae_desafiante"]] * len(anios)
        contexto["svg_momento_optimo"] = construir_svg_dos_series(
            anios, cae_actual_serie, cae_desafiante_serie,
            nombre_actual=d["nombre_actual"], nombre_desafiante=d["nombre_desafiante"],
            n_cruce=resultado.n_optimo if resultado.n_optimo > 0 else None,
        )
        contexto["cae_desafiante_json"] = json.dumps([round(v, 1) for v in cae_desafiante_serie])
        contexto["nombre_actual"] = d["nombre_actual"]
        contexto["nombre_desafiante"] = d["nombre_desafiante"]

    return render(request, "reemplazo_equipos/momento_optimo.html", contexto)
