"""
finance_engine.riesgo
=======================
Unidad V generalizada: análisis de sensibilidad (univariado y tornado),
análisis de escenarios, árboles de decisión y una aproximación simple de
opciones reales (opción de abandono/expansión vía árbol binomial, y
Black-Scholes para opción de espera).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .evaluacion import FinanceEngineError, calcular_van


# ---------------------------------------------------------------------------
# Análisis de sensibilidad
# ---------------------------------------------------------------------------
@dataclass
class PuntoSensibilidad:
    variacion_pct: float
    valor_variable: float
    van_resultante: float


@dataclass
class ResultadoSensibilidad:
    nombre_variable: str
    valor_base: float
    van_base: float
    puntos: list = field(default_factory=list)
    interpretacion: str = ""


def analisis_sensibilidad_univariado(
    nombre_variable: str,
    valor_base: float,
    construir_flujos: Callable[[float], Sequence[float]],
    tasa_descuento: float,
    variaciones_pct: Sequence[float] = (-0.20, -0.10, 0.0, 0.10, 0.20),
) -> ResultadoSensibilidad:
    """
    Recalcula el VAN variando una sola variable en los porcentajes indicados.
    'construir_flujos' es una función que recibe el nuevo valor de la
    variable y devuelve el flujo de caja completo del proyecto.
    """
    puntos = []
    van_base = None
    for variacion in variaciones_pct:
        nuevo_valor = valor_base * (1 + variacion)
        flujos = construir_flujos(nuevo_valor)
        van = calcular_van(flujos, tasa_descuento).valor
        puntos.append(PuntoSensibilidad(variacion_pct=variacion, valor_variable=nuevo_valor, van_resultante=van))
        if variacion == 0.0:
            van_base = van

    if van_base is None:
        van_base = calcular_van(construir_flujos(valor_base), tasa_descuento).valor

    rango_van = max(p.van_resultante for p in puntos) - min(p.van_resultante for p in puntos)

    return ResultadoSensibilidad(
        nombre_variable=nombre_variable,
        valor_base=valor_base,
        van_base=van_base,
        puntos=puntos,
        interpretacion=(
            f"Al variar '{nombre_variable}' entre {min(variaciones_pct) * 100:.0f}% y "
            f"{max(variaciones_pct) * 100:.0f}% respecto a su valor base, el VAN se mueve en "
            f"un rango de ${rango_van:,.0f}. Cuanto mayor sea este rango, más sensible es el "
            "proyecto a esta variable, y por lo tanto más riesgo propio aporta: conviene "
            "vigilarla de cerca durante la ejecución del proyecto."
        ),
    )


def construir_tornado(resultados: Sequence[ResultadoSensibilidad]) -> list:
    """
    Ordena variables por impacto en el VAN (rango máx-mín), de mayor a menor,
    para construir un 'gráfico de tornado' — la salida estándar de cualquier
    análisis de sensibilidad multivariable.
    """
    filas = []
    for r in resultados:
        rango = max(p.van_resultante for p in r.puntos) - min(p.van_resultante for p in r.puntos)
        filas.append({"variable": r.nombre_variable, "rango_van": rango, "detalle": r})
    filas.sort(key=lambda f: f["rango_van"], reverse=True)
    return filas


# ---------------------------------------------------------------------------
# Análisis de escenarios (pesimista / base / optimista, con valor esperado)
# ---------------------------------------------------------------------------
@dataclass
class Escenario:
    nombre: str
    probabilidad: float
    flujos: Sequence[float]


@dataclass
class ResultadoEscenarios:
    escenarios: list
    vanes: dict = field(default_factory=dict)
    van_esperado: float = 0.0
    desviacion_estandar: float = 0.0
    interpretacion: str = ""


def analisis_escenarios(escenarios: Sequence[Escenario], tasa_descuento: float) -> ResultadoEscenarios:
    suma_prob = sum(e.probabilidad for e in escenarios)
    if abs(suma_prob - 1.0) > 1e-3:
        raise FinanceEngineError(f"Las probabilidades deben sumar 1.0 (suman {suma_prob:.3f}).")

    vanes = {e.nombre: calcular_van(e.flujos, tasa_descuento).valor for e in escenarios}
    van_esperado = sum(vanes[e.nombre] * e.probabilidad for e in escenarios)
    varianza = sum(e.probabilidad * (vanes[e.nombre] - van_esperado) ** 2 for e in escenarios)
    desviacion = math.sqrt(varianza)

    coef_variacion = desviacion / abs(van_esperado) if van_esperado != 0 else float("inf")

    return ResultadoEscenarios(
        escenarios=list(escenarios),
        vanes=vanes,
        van_esperado=van_esperado,
        desviacion_estandar=desviacion,
        interpretacion=(
            f"El VAN esperado (promedio ponderado por probabilidad) es ${van_esperado:,.0f}, "
            f"con una desviación estándar de ${desviacion:,.0f} (coeficiente de variación "
            f"{coef_variacion:.2f}). Mientras más alto el coeficiente de variación, mayor es "
            "el riesgo propio del proyecto en relación a su rentabilidad esperada: dos "
            "proyectos con igual VAN esperado pueden tener niveles de riesgo muy distintos."
        ),
    )


# ---------------------------------------------------------------------------
# Árboles de decisión
# ---------------------------------------------------------------------------
@dataclass
class NodoDecision:
    nombre: str
    es_decision: bool                  # True = nodo de decisión (elige el mejor); False = nodo de azar (valor esperado)
    hijos: list = field(default_factory=list)   # lista de (NodoDecision | None, probabilidad_o_None, flujo_asociado)
    valor_calculado: float | None = None
    opcion_elegida: str | None = None


def evaluar_arbol_decision(nodo: NodoDecision) -> float:
    """
    Evalúa recursivamente un árbol de decisión "hacia atrás" (rollback):
    - En nodos de azar: valor = suma(prob_i * (flujo_i + valor(hijo_i)))
    - En nodos de decisión: valor = max sobre las ramas (flujo_i + valor(hijo_i))
    """
    if not nodo.hijos:
        nodo.valor_calculado = 0.0
        return 0.0

    valores_rama = []
    for hijo, prob, flujo in nodo.hijos:
        valor_hijo = evaluar_arbol_decision(hijo) if hijo is not None else 0.0
        valores_rama.append((flujo + valor_hijo, prob))

    if nodo.es_decision:
        mejor_idx = max(range(len(valores_rama)), key=lambda i: valores_rama[i][0])
        nodo.valor_calculado = valores_rama[mejor_idx][0]
        nodo.opcion_elegida = nodo.hijos[mejor_idx][0].nombre if nodo.hijos[mejor_idx][0] else f"rama_{mejor_idx}"
    else:
        nodo.valor_calculado = sum(v * (p or 0) for v, p in valores_rama)

    return nodo.valor_calculado


# ---------------------------------------------------------------------------
# Opciones reales — Black-Scholes para opción de espera/expansión (estilo europeo)
# ---------------------------------------------------------------------------
def _norm_cdf(x: float) -> float:
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


@dataclass
class ResultadoOpcionReal:
    valor_opcion: float
    d1: float
    d2: float
    interpretacion: str = ""


def opcion_real_black_scholes(
    valor_activo_subyacente: float,
    precio_ejercicio: float,
    tasa_libre_riesgo: float,
    volatilidad: float,
    tiempo_anos: float,
) -> ResultadoOpcionReal:
    """
    Valora una opción real tipo "call" (ej. opción de expandir o esperar para
    invertir) usando Black-Scholes:
        S = valor presente de los flujos del proyecto si se invierte ahora
        K = inversión requerida (precio de ejercicio)
        sigma = volatilidad del valor del proyecto
        T = tiempo durante el cual existe la opción de esperar/expandir
    """
    if volatilidad <= 0 or tiempo_anos <= 0:
        raise FinanceEngineError("Volatilidad y tiempo deben ser mayores a cero.")

    d1 = (
        math.log(valor_activo_subyacente / precio_ejercicio)
        + (tasa_libre_riesgo + 0.5 * volatilidad ** 2) * tiempo_anos
    ) / (volatilidad * math.sqrt(tiempo_anos))
    d2 = d1 - volatilidad * math.sqrt(tiempo_anos)

    valor = (
        valor_activo_subyacente * _norm_cdf(d1)
        - precio_ejercicio * math.exp(-tasa_libre_riesgo * tiempo_anos) * _norm_cdf(d2)
    )

    return ResultadoOpcionReal(
        valor_opcion=valor,
        d1=d1,
        d2=d2,
        interpretacion=(
            f"El valor de la opción real (flexibilidad de esperar/expandir) es ${valor:,.0f}. "
            "Este valor se suma al VAN tradicional ('VAN expandido' = VAN estático + valor de "
            "la opción). Mientras mayor sea la incertidumbre (volatilidad) y más tiempo exista "
            "la opción, más valiosa es la flexibilidad de postergar o ampliar la decisión de "
            "inversión en vez de decidir todo hoy de forma irreversible."
        ),
    )
