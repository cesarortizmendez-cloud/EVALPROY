"""
finance_engine.no_periodicos
==============================
VAN y TIR para flujos NO periódicos (con fechas reales, replicando las
funciones VAN.NO.PER y TIR.NO.PER de Excel — en inglés XNPV/XIRR).

A diferencia del VAN/TIR "normal" (que asume un flujo exactamente cada
año), aquí cada flujo tiene una fecha específica y el descuento se hace
sobre los días reales transcurridos desde la fecha del primer flujo,
usando una convención de año de 365 días — igual que Excel.

    XNPV = Σ  CFᵢ / (1 + tasa) ^ ((fechaᵢ - fecha₀) / 365)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from .evaluacion import FinanceEngineError


@dataclass
class ResultadoVanNoPeriodico:
    valor: float
    tasa: float
    fechas: Sequence[date]
    flujos: Sequence[float]
    dias_desde_inicio: list
    interpretacion: str = ""
    semaforo: str = ""


def calcular_van_no_periodico(fechas: Sequence[date], flujos: Sequence[float], tasa: float) -> ResultadoVanNoPeriodico:
    """
    Replica VAN.NO.PER de Excel: el primer flujo (fechas[0], flujos[0]) se
    descuenta a t=0 (no se actualiza), y los siguientes se descuentan según
    los días reales transcurridos desde esa primera fecha, base 365 días.
    """
    if len(fechas) != len(flujos):
        raise FinanceEngineError("Debe haber la misma cantidad de fechas que de flujos.")
    if len(fechas) < 2:
        raise FinanceEngineError("Debe ingresar al menos dos flujos (inversión y un retorno).")
    if tasa <= -1:
        raise FinanceEngineError("La tasa de descuento debe ser mayor a -100%.")
    if any(fechas[i] < fechas[0] for i in range(len(fechas))):
        raise FinanceEngineError("Todas las fechas deben ser iguales o posteriores a la primera fecha.")

    fecha_0 = fechas[0]
    dias = [(f - fecha_0).days for f in fechas]
    van = sum(flujo / ((1 + tasa) ** (d / 365)) for flujo, d in zip(flujos, dias))

    return ResultadoVanNoPeriodico(valor=van, tasa=tasa, fechas=list(fechas), flujos=list(flujos), dias_desde_inicio=dias)


def interpretar_van_no_periodico(resultado: ResultadoVanNoPeriodico) -> ResultadoVanNoPeriodico:
    if resultado.valor > 0:
        resultado.semaforo = "positivo"
        resultado.interpretacion = (
            f"El VAN (no periódico) es positivo (${resultado.valor:,.2f}). Aun con flujos irregulares "
            f"en el tiempo, el proyecto genera más valor del que cuesta financiarlo a una tasa de "
            f"{resultado.tasa * 100:.2f}%: conviene aceptarlo."
        )
    elif resultado.valor < 0:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            f"El VAN (no periódico) es negativo (${resultado.valor:,.2f}). El proyecto no alcanza a cubrir "
            f"el costo de oportunidad del capital ({resultado.tasa * 100:.2f}%) dado el calendario real de "
            "flujos: conviene rechazarlo."
        )
    else:
        resultado.semaforo = "neutro"
        resultado.interpretacion = "El VAN (no periódico) es exactamente cero: el proyecto rinde justo la tasa exigida."
    return resultado


@dataclass
class ResultadoTirNoPeriodico:
    valor: float | None
    convergio: bool
    interpretacion: str = ""
    semaforo: str = ""


def _xnpv(fechas: Sequence[date], flujos: Sequence[float], tasa: float) -> float:
    fecha_0 = fechas[0]
    return sum(flujo / ((1 + tasa) ** ((f - fecha_0).days / 365)) for flujo, f in zip(flujos, fechas))


def calcular_tir_no_periodico(
    fechas: Sequence[date], flujos: Sequence[float],
    estimacion_inicial: float = 0.10, tolerancia: float = 1e-7, max_iteraciones: int = 200,
) -> ResultadoTirNoPeriodico:
    """
    Replica TIR.NO.PER de Excel: encuentra la tasa que hace VAN.NO.PER = 0,
    usando bisección sobre el rango (-0.99, 10.0) por robustez (evita
    depender de derivadas con exponentes fraccionarios irregulares).
    """
    if len(fechas) != len(flujos):
        raise FinanceEngineError("Debe haber la misma cantidad de fechas que de flujos.")
    if len(fechas) < 2:
        raise FinanceEngineError("Debe ingresar al menos dos flujos (inversión y un retorno).")

    lo, hi = -0.99, 10.0
    van_lo, van_hi = _xnpv(fechas, flujos, lo), _xnpv(fechas, flujos, hi)
    if van_lo * van_hi > 0:
        return ResultadoTirNoPeriodico(valor=None, convergio=False)

    for _ in range(max_iteraciones):
        mid = (lo + hi) / 2
        van_mid = _xnpv(fechas, flujos, mid)
        if abs(van_mid) < tolerancia:
            return ResultadoTirNoPeriodico(valor=mid, convergio=True)
        if van_lo * van_mid < 0:
            hi = mid
        else:
            lo, van_lo = mid, van_mid

    return ResultadoTirNoPeriodico(valor=(lo + hi) / 2, convergio=True)


def interpretar_tir_no_periodico(resultado: ResultadoTirNoPeriodico, tasa_corte: float | None = None) -> ResultadoTirNoPeriodico:
    if not resultado.convergio or resultado.valor is None:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            "No fue posible encontrar una TIR real con este calendario de flujos. Revisa que exista al "
            "menos un cambio de signo entre los flujos."
        )
        return resultado

    pct = resultado.valor * 100
    if tasa_corte is None:
        resultado.semaforo = "neutro"
        resultado.interpretacion = f"La TIR (no periódica) del proyecto es {pct:.2f}%."
    elif resultado.valor > tasa_corte:
        resultado.semaforo = "positivo"
        resultado.interpretacion = (
            f"La TIR ({pct:.2f}%) es mayor que la tasa de corte ({tasa_corte * 100:.2f}%): el proyecto "
            "rinde más de lo que cuesta financiarlo, incluso con flujos en fechas irregulares."
        )
    elif resultado.valor < tasa_corte:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            f"La TIR ({pct:.2f}%) es menor que la tasa de corte ({tasa_corte * 100:.2f}%): conviene rechazar el proyecto."
        )
    else:
        resultado.semaforo = "neutro"
        resultado.interpretacion = f"La TIR ({pct:.2f}%) es igual a la tasa de corte: es el punto de indiferencia."
    return resultado
