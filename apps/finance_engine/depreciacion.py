"""
finance_engine.depreciacion
============================
Cálculo de depreciación normal (lineal) y acelerada (suma de dígitos)
para la construcción de flujos de caja de proyectos.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .evaluacion import FinanceEngineError


@dataclass
class ResultadoDepreciacion:
    metodo: str
    valor_activo: float
    valor_residual: float
    vida_util: int
    cuotas_anuales: list = field(default_factory=list)
    valor_libro: list = field(default_factory=list)
    interpretacion: str = ""


def depreciacion_lineal(valor_activo: float, valor_residual: float, vida_util: int) -> ResultadoDepreciacion:
    if vida_util <= 0:
        raise FinanceEngineError("La vida útil debe ser mayor a cero.")
    if valor_residual > valor_activo:
        raise FinanceEngineError("El valor residual no puede ser mayor al valor del activo.")

    cuota = (valor_activo - valor_residual) / vida_util
    cuotas = [cuota] * vida_util

    valor_libro = []
    saldo = valor_activo
    for c in cuotas:
        saldo -= c
        valor_libro.append(saldo)

    return ResultadoDepreciacion(
        metodo="lineal",
        valor_activo=valor_activo,
        valor_residual=valor_residual,
        vida_util=vida_util,
        cuotas_anuales=cuotas,
        valor_libro=valor_libro,
        interpretacion=(
            f"Con depreciación normal (lineal), el activo se deprecia en cuotas iguales de "
            f"${cuota:,.0f} durante {vida_util} años. Es el método más simple, pero no genera "
            "el mayor escudo tributario posible en los primeros años, a diferencia de la "
            "depreciación acelerada."
        ),
    )


def depreciacion_acelerada_suma_digitos(valor_activo: float, valor_residual: float, vida_util: int) -> ResultadoDepreciacion:
    if vida_util <= 0:
        raise FinanceEngineError("La vida útil debe ser mayor a cero.")
    if valor_residual > valor_activo:
        raise FinanceEngineError("El valor residual no puede ser mayor al valor del activo.")

    base_depreciable = valor_activo - valor_residual
    suma_digitos = vida_util * (vida_util + 1) / 2

    cuotas = []
    for anio in range(1, vida_util + 1):
        peso = (vida_util - anio + 1) / suma_digitos
        cuotas.append(base_depreciable * peso)

    valor_libro = []
    saldo = valor_activo
    for c in cuotas:
        saldo -= c
        valor_libro.append(saldo)

    return ResultadoDepreciacion(
        metodo="acelerada_suma_digitos",
        valor_activo=valor_activo,
        valor_residual=valor_residual,
        vida_util=vida_util,
        cuotas_anuales=cuotas,
        valor_libro=valor_libro,
        interpretacion=(
            f"Con depreciación acelerada (suma de dígitos), el primer año se deprecia "
            f"${cuotas[0]:,.0f} y la cuota decrece cada año. Esto adelanta el escudo "
            "tributario: la empresa paga menos impuestos en los primeros años del proyecto, "
            "lo que -al traer esos ahorros a valor presente- mejora el VAN respecto al "
            "método lineal, aunque la depreciación total acumulada es la misma."
        ),
    )


def comparar_metodos_depreciacion(valor_activo: float, valor_residual: float, vida_util: int,
                                   tasa_impuesto: float, tasa_descuento: float) -> dict:
    lineal = depreciacion_lineal(valor_activo, valor_residual, vida_util)
    acelerada = depreciacion_acelerada_suma_digitos(valor_activo, valor_residual, vida_util)

    vp_escudo_lineal = sum(
        (c * tasa_impuesto) / ((1 + tasa_descuento) ** (i + 1))
        for i, c in enumerate(lineal.cuotas_anuales)
    )
    vp_escudo_acelerada = sum(
        (c * tasa_impuesto) / ((1 + tasa_descuento) ** (i + 1))
        for i, c in enumerate(acelerada.cuotas_anuales)
    )
    diferencia = vp_escudo_acelerada - vp_escudo_lineal

    return {
        "lineal": lineal,
        "acelerada": acelerada,
        "vp_escudo_lineal": vp_escudo_lineal,
        "vp_escudo_acelerada": vp_escudo_acelerada,
        "diferencia": diferencia,
        "interpretacion": (
            f"El valor presente del escudo tributario es ${vp_escudo_lineal:,.0f} con el método "
            f"lineal y ${vp_escudo_acelerada:,.0f} con el método acelerado. La depreciación "
            f"acelerada aporta ${diferencia:,.0f} adicionales de valor presente solo por "
            "adelantar el ahorro de impuestos en el tiempo."
        ),
    }
