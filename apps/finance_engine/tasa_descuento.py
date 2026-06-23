"""
finance_engine.tasa_descuento
===============================
Costo del patrimonio (CAPM), costo de la deuda, WACC y ajuste de beta
(apalancado/desapalancado) — Unidad IV del syllabus, generalizada.
"""
from __future__ import annotations

from dataclasses import dataclass

from .evaluacion import FinanceEngineError


@dataclass
class ResultadoCAPM:
    ke: float
    tasa_libre_riesgo: float
    beta: float
    premio_mercado: float
    interpretacion: str = ""


def costo_patrimonio_capm(tasa_libre_riesgo: float, beta: float, premio_riesgo_mercado: float) -> ResultadoCAPM:
    """
    Ke = Rf + Beta * (Rm - Rf)
    'premio_riesgo_mercado' puede pasarse ya como (Rm - Rf) o se puede
    calcular fuera; aquí se asume que es el premio (Rm - Rf) directamente.
    """
    ke = tasa_libre_riesgo + beta * premio_riesgo_mercado
    resultado = ResultadoCAPM(
        ke=ke,
        tasa_libre_riesgo=tasa_libre_riesgo,
        beta=beta,
        premio_mercado=premio_riesgo_mercado,
    )
    resultado.interpretacion = (
        f"El costo del patrimonio (Ke) es {ke * 100:.2f}%. Según CAPM, los inversionistas "
        f"exigen la tasa libre de riesgo ({tasa_libre_riesgo * 100:.2f}%) más un premio por "
        f"riesgo sistemático: Beta ({beta:.2f}) multiplicado por el premio de mercado "
        f"({premio_riesgo_mercado * 100:.2f}%). Un Beta > 1 indica que el proyecto es más "
        "riesgoso que el mercado (amplifica sus movimientos); Beta < 1 indica lo contrario."
    )
    return resultado


def desapalancar_beta(beta_apalancado: float, deuda: float, patrimonio: float, tasa_impuesto: float) -> float:
    """Fórmula de Hamada: Beta desapalancado (del activo, sin efecto de deuda)."""
    if patrimonio <= 0:
        raise FinanceEngineError("El patrimonio debe ser mayor a cero.")
    return beta_apalancado / (1 + (1 - tasa_impuesto) * (deuda / patrimonio))


def apalancar_beta(beta_desapalancado: float, deuda: float, patrimonio: float, tasa_impuesto: float) -> float:
    """Fórmula de Hamada inversa: Beta apalancado dado el nivel de deuda del proyecto."""
    if patrimonio <= 0:
        raise FinanceEngineError("El patrimonio debe ser mayor a cero.")
    return beta_desapalancado * (1 + (1 - tasa_impuesto) * (deuda / patrimonio))


@dataclass
class ResultadoWACC:
    wacc: float
    ke: float
    kd: float
    porcentaje_patrimonio: float
    porcentaje_deuda: float
    tasa_impuesto: float
    interpretacion: str = ""


def calcular_wacc(ke: float, kd: float, valor_patrimonio: float, valor_deuda: float, tasa_impuesto: float) -> ResultadoWACC:
    """
    WACC = (E/V)*Ke + (D/V)*Kd*(1 - t)
    donde V = E + D.
    """
    valor_total = valor_patrimonio + valor_deuda
    if valor_total <= 0:
        raise FinanceEngineError("La suma de patrimonio y deuda debe ser mayor a cero.")

    pct_e = valor_patrimonio / valor_total
    pct_d = valor_deuda / valor_total
    wacc = pct_e * ke + pct_d * kd * (1 - tasa_impuesto)

    resultado = ResultadoWACC(
        wacc=wacc, ke=ke, kd=kd,
        porcentaje_patrimonio=pct_e, porcentaje_deuda=pct_d,
        tasa_impuesto=tasa_impuesto,
    )
    resultado.interpretacion = (
        f"El WACC (tasa de corte del proyecto) es {wacc * 100:.2f}%. Se compone de "
        f"{pct_e * 100:.1f}% financiado con patrimonio (costo {ke * 100:.2f}%) y "
        f"{pct_d * 100:.1f}% con deuda (costo {kd * 100:.2f}%, reducido por el escudo "
        f"tributario de la deuda al multiplicarse por (1 - {tasa_impuesto * 100:.0f}%)). "
        "Esta es la tasa que debes usar para descontar los flujos del proyecto y calcular "
        "su VAN: si el proyecto rinde menos que el WACC, destruye valor."
    )
    return resultado
