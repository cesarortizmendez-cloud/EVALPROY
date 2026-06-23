"""
finance_engine.reemplazo
==========================
Reemplazo de equipos: dos herramientas clásicas del capítulo de
"momento óptimo para reemplazar un equipo" (Gutiérrez, 1994; apunte UNAB):

1) Vida económica de un equipo nuevo, por el método del Costo Anual
   Equivalente (CAE): se "tantea" el n óptimo con la fórmula aproximada
   y luego se confirma calculando el CAE exacto en la vecindad de ese n.

2) Momento óptimo de reemplazo entre dos alternativas (equipo desafiante
   vs. equipo defensor, o proceso automático vs. proceso manual), cuando
   el costo de la alternativa actual crece a una tasa conocida.

También se mantiene el CAUE genérico (para comparar alternativas de
distinta vida con costos arbitrarios año a año, usado en el módulo de
flujo de caja / comparaciones generales).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from .evaluacion import FinanceEngineError


# ---------------------------------------------------------------------------
# CAUE genérico (costos arbitrarios año a año) — se mantiene para otros usos
# ---------------------------------------------------------------------------
@dataclass
class ResultadoCAUE:
    caue: float
    valor_presente_costos: float
    vida_util: int
    tasa: float
    interpretacion: str = ""


def factor_recuperacion_capital(tasa: float, n: int) -> float:
    if tasa == 0:
        return 1 / n
    return (tasa * (1 + tasa) ** n) / ((1 + tasa) ** n - 1)


def calcular_caue(costos_anuales: Sequence[float], inversion_inicial: float, valor_salvamento: float, tasa: float) -> ResultadoCAUE:
    n = len(costos_anuales)
    if n == 0:
        raise FinanceEngineError("Debe ingresar al menos un año de costos de operación.")

    vp_costos_operacion = sum(c / ((1 + tasa) ** (t + 1)) for t, c in enumerate(costos_anuales))
    vp_salvamento = valor_salvamento / ((1 + tasa) ** n)
    vp_total = inversion_inicial + vp_costos_operacion - vp_salvamento

    factor = factor_recuperacion_capital(tasa, n)
    caue = vp_total * factor

    return ResultadoCAUE(
        caue=caue, valor_presente_costos=vp_total, vida_util=n, tasa=tasa,
        interpretacion=(
            f"El Costo Anual Uniforme Equivalente (CAUE) de mantener este equipo durante "
            f"{n} años es ${caue:,.0f} por año."
        ),
    )


def comparar_caue_alternativas(alternativas: dict) -> dict:
    if not alternativas:
        raise FinanceEngineError("Debe ingresar al menos una alternativa.")
    nombre_mejor = min(alternativas, key=lambda k: alternativas[k].caue)
    mejor = alternativas[nombre_mejor]
    return {
        "mejor_alternativa": nombre_mejor,
        "caue_mejor": mejor.caue,
        "detalle": alternativas,
        "interpretacion": (
            f"Comparando el CAUE de cada alternativa, '{nombre_mejor}' tiene el menor costo "
            f"anual equivalente (${mejor.caue:,.0f}/año) y por lo tanto es la opción más eficiente."
        ),
    }


# ---------------------------------------------------------------------------
# 1) VIDA ECONÓMICA con gradiente de deterioro (g) — método de tanteo + CAE
#
# Fórmula aproximada (Gutiérrez, 1994, ec. 8.2 / apunte UNAB):
#   n* ≈ (P*i)/g + 1/i − 1 / [ i * (1+i)^n ]
#
# Como n aparece en ambos lados, se resuelve por TANTEO: se prueba un rango
# de valores de n, se calcula el "n resultante" de la fórmula, y se elige
# el n tanteado más cercano a su propio resultado. Luego se confirma
# calculando el CAE exacto en la vecindad de ese n, eligiendo el mínimo.
# ---------------------------------------------------------------------------
@dataclass
class FilaTanteo:
    n_tanteado: int
    n_resultante: float
    diferencia: float


@dataclass
class FilaCAE:
    n: int
    cae: float
    es_minimo: bool = False


@dataclass
class ResultadoVidaEconomica:
    P: float
    A: float
    g: float
    i: float
    tabla_tanteo: list = field(default_factory=list)
    n_tanteado_elegido: int = 0
    tabla_cae: list = field(default_factory=list)
    n_optimo: int = 0
    cae_minimo: float = 0.0
    interpretacion_tanteo: str = ""
    interpretacion_final: str = ""


def _n_resultante(P: float, A: float, g: float, i: float, n: int) -> float:
    """Lado derecho de la fórmula aproximada de tanteo (8.2)."""
    if n <= 0 or i <= 0:
        raise FinanceEngineError("La tasa y el número de años deben ser mayores a cero.")
    return (P * i) / g + (1 / i) - (1 / (i * (1 + i) ** n))


def _cae_exacto(P: float, A: float, g: float, i: float, n: int) -> float:
    """
    CAE exacto (no aproximado) para un n dado, usando la fórmula con el
    factor de recuperación de capital y el gradiente aritmético g:
        CAE = P * FRC(i,n) + A + g * [ 1/i − n / ((1+i)^n − 1) ]
    """
    frc = factor_recuperacion_capital(i, n)
    factor_gradiente = (1 / i) - (n / ((1 + i) ** n - 1))
    return P * frc + A + g * factor_gradiente


def calcular_vida_economica(
    P: float, A: float, g: float, i: float,
    rango_tanteo: Sequence[int] = tuple(range(10, 21)),
) -> ResultadoVidaEconomica:
    """
    Replica exactamente el procedimiento del Excel del curso:
    1. Para cada n en 'rango_tanteo', calcula el n_resultante de la fórmula
       aproximada y la diferencia |n_tanteado - n_resultante| (tabla de
       tanteo, columnas D y E del Excel).
    2. Para ESE MISMO rango completo de n, calcula el CAE exacto (tabla de
       confirmación, columnas D y E más abajo en el Excel) y elige el
       verdadero óptimo: el de menor CAE. No se reduce a una ventana
       pequeña: se muestra el rango íntegro que el estudiante definió,
       igual que en la planilla.
    """
    if g == 0:
        raise FinanceEngineError("El gradiente de deterioro (g) no puede ser cero en este método.")
    if i <= 0:
        raise FinanceEngineError("La tasa de descuento (i) debe ser mayor a cero.")

    rango_tanteo = list(rango_tanteo)

    tabla_tanteo = []
    for n in rango_tanteo:
        n_res = _n_resultante(P, A, g, i, n)
        tabla_tanteo.append(FilaTanteo(n_tanteado=n, n_resultante=n_res, diferencia=abs(n - n_res)))

    fila_elegida = min(tabla_tanteo, key=lambda f: f.diferencia)
    n_elegido = fila_elegida.n_tanteado

    tabla_cae = []
    for n in rango_tanteo:
        cae = _cae_exacto(P, A, g, i, n)
        tabla_cae.append(FilaCAE(n=n, cae=cae))

    fila_minima = min(tabla_cae, key=lambda f: f.cae)
    fila_minima.es_minimo = True
    n_optimo = fila_minima.n
    cae_minimo = fila_minima.cae

    interpretacion_tanteo = (
        f"Probando distintos valores de n en la fórmula aproximada, el valor que más se "
        f"acerca a sí mismo (n tanteado ≈ n resultante) es n = {n_elegido} años. Este es solo "
        "un punto de partida: la fórmula aproximada usa ln(1+i)≈i, así que el verdadero óptimo "
        "puede estar a 1 o 2 años de distancia y se confirma calculando el CAE exacto."
    )
    interpretacion_final = (
        f"Calculando el Costo Anual Equivalente exacto para los años cercanos a {n_elegido}, "
        f"el mínimo se alcanza en n = {n_optimo} años, con un CAE de ${cae_minimo:,.0f}. "
        f"Esto significa que conviene usar el equipo durante {n_optimo} años antes de "
        "reemplazarlo por uno igual: usarlo menos o más tiempo que eso resulta en un costo "
        "anual equivalente mayor."
    )

    return ResultadoVidaEconomica(
        P=P, A=A, g=g, i=i,
        tabla_tanteo=tabla_tanteo, n_tanteado_elegido=n_elegido,
        tabla_cae=tabla_cae, n_optimo=n_optimo, cae_minimo=cae_minimo,
        interpretacion_tanteo=interpretacion_tanteo,
        interpretacion_final=interpretacion_final,
    )


# ---------------------------------------------------------------------------
# 2) MOMENTO ÓPTIMO DE REEMPLAZO (desafiante vs. defensora/manual, con
#    crecimiento conocido de la alternativa actual)
#
# Fórmula (apartado "¿Qué es más conveniente..." del apunte UNAB):
#   n* ≥ ln( CAE_desafiante / CAE_actual ) / ln( 1 + tasa_incremento )
# ---------------------------------------------------------------------------
@dataclass
class ResultadoMomentoOptimo:
    cae_desafiante: float
    cae_actual: float
    tasa_incremento: float
    n_optimo: float
    interpretacion: str = ""


def calcular_momento_optimo_reemplazo(cae_desafiante: float, cae_actual: float, tasa_incremento: float) -> ResultadoMomentoOptimo:
    """
    cae_desafiante: CAE del equipo/proceso nuevo (constante, no crece).
    cae_actual: CAE de la alternativa que se sigue usando hoy (defensora o
                proceso manual), que crece a 'tasa_incremento' cada año.
    Devuelve el n* (años) a partir del cual conviene reemplazar.
    """
    if cae_actual <= 0 or cae_desafiante <= 0:
        raise FinanceEngineError("Los CAE deben ser valores positivos.")
    if tasa_incremento <= -1:
        raise FinanceEngineError("La tasa de incremento debe ser mayor a -100%.")

    if cae_desafiante <= cae_actual:
        n_optimo = 0.0
    else:
        n_optimo = math.log(cae_desafiante / cae_actual) / math.log(1 + tasa_incremento)

    if n_optimo <= 0:
        interpretacion = (
            f"El CAE del equipo desafiante (${cae_desafiante:,.0f}) ya es menor o igual al CAE "
            f"actual (${cae_actual:,.0f}): conviene reemplazar de inmediato, sin esperar."
        )
    else:
        anio_entero = math.ceil(n_optimo)
        interpretacion = (
            f"Hoy el equipo desafiante (${cae_desafiante:,.0f}/año) es más caro que la "
            f"alternativa actual (${cae_actual:,.0f}/año), pero esta última crece a una tasa de "
            f"{tasa_incremento * 100:.2f}% anual. Ambos CAE se igualan en n* = {n_optimo:.2f} "
            f"años: a partir del año {anio_entero}, conviene reemplazar, porque desde ese momento "
            "el costo de seguir con la alternativa actual supera al del equipo desafiante."
        )

    return ResultadoMomentoOptimo(
        cae_desafiante=cae_desafiante, cae_actual=cae_actual,
        tasa_incremento=tasa_incremento, n_optimo=n_optimo,
        interpretacion=interpretacion,
    )
