"""
finance_engine.evaluacion
=========================
Motor puro (sin Django) para los criterios clásicos de evaluación de
proyectos de inversión: VAN, TIR, Payback, Tasa de Fisher e IVAN.

Convención usada en todo el motor:
    flujos: list[float]  -> flujos[0] es la inversión inicial (negativa
                             por convención) y flujos[1:] son los flujos
                             futuros (positivos o negativos).
    tasa:   float        -> tasa de descuento anual en decimal (0.10 = 10%)

Cada función de cálculo "calcular_x" tiene una función hermana
"interpretar_x" que traduce el resultado numérico a una explicación en
lenguaje natural + un nivel de semáforo ("positivo", "neutro", "negativo"),
pensada para mostrarse directamente en la interfaz junto al resultado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


# ---------------------------------------------------------------------------
# Excepciones propias del motor
# ---------------------------------------------------------------------------
class FinanceEngineError(Exception):
    """Error de dominio (datos inválidos), no un error de programación."""


# ---------------------------------------------------------------------------
# Estructuras de resultado
# ---------------------------------------------------------------------------
@dataclass
class ResultadoVAN:
    valor: float
    tasa: float
    flujos: Sequence[float]
    valores_presentes: list[float] = field(default_factory=list)
    interpretacion: str = ""
    semaforo: str = ""  # "positivo" | "neutro" | "negativo"


@dataclass
class ResultadoTIR:
    valor: float | None          # None si no converge / no existe
    iteraciones: int
    convergio: bool
    interpretacion: str = ""
    semaforo: str = ""


@dataclass
class ResultadoPayback:
    periodo: float | None        # en años (puede ser fraccionario), None si nunca se recupera
    flujo_acumulado: list[float] = field(default_factory=list)
    interpretacion: str = ""
    semaforo: str = ""


# ---------------------------------------------------------------------------
# VAN (Valor Actual Neto)
# ---------------------------------------------------------------------------
def calcular_van(flujos: Sequence[float], tasa: float) -> ResultadoVAN:
    """
    VAN = sum( flujo_t / (1+tasa)^t )  para t = 0..n

    flujos[0] es t=0 (normalmente la inversión inicial, negativa).
    """
    if not flujos:
        raise FinanceEngineError("Debe ingresar al menos un flujo de caja.")
    if tasa <= -1:
        raise FinanceEngineError("La tasa de descuento debe ser mayor a -100%.")

    valores_presentes = [
        flujo / ((1 + tasa) ** t) for t, flujo in enumerate(flujos)
    ]
    van = sum(valores_presentes)

    return ResultadoVAN(
        valor=van,
        tasa=tasa,
        flujos=list(flujos),
        valores_presentes=valores_presentes,
    )


def interpretar_van(resultado: ResultadoVAN) -> ResultadoVAN:
    if resultado.valor > 0:
        resultado.semaforo = "positivo"
        resultado.interpretacion = (
            f"El VAN es positivo (${resultado.valor:,.0f}). Esto significa que, "
            f"descontando los flujos a una tasa de {resultado.tasa * 100:.2f}%, el proyecto "
            "genera más valor del que cuesta financiarlo: se recupera la inversión, se paga "
            "el costo del capital y queda un excedente. Conclusión: el proyecto crea valor y "
            "conviene aceptarlo."
        )
    elif resultado.valor < 0:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            f"El VAN es negativo (${resultado.valor:,.0f}). El proyecto no alcanza a cubrir "
            f"el costo de oportunidad del capital ({resultado.tasa * 100:.2f}%): destruye valor "
            "en vez de crearlo. Conclusión: el proyecto debería rechazarse, salvo que existan "
            "razones estratégicas no monetarias para aceptarlo."
        )
    else:
        resultado.semaforo = "neutro"
        resultado.interpretacion = (
            "El VAN es exactamente cero: el proyecto rinde justo la tasa de descuento exigida, "
            "ni más ni menos. Es el punto de indiferencia entre aceptar y rechazar."
        )
    return resultado


# ---------------------------------------------------------------------------
# TIR (Tasa Interna de Retorno) — método de Newton-Raphson con respaldo bisección
# ---------------------------------------------------------------------------
def _van_de(flujos: Sequence[float], tasa: float) -> float:
    return sum(flujo / ((1 + tasa) ** t) for t, flujo in enumerate(flujos))


def _van_derivada(flujos: Sequence[float], tasa: float) -> float:
    return sum(
        -t * flujo / ((1 + tasa) ** (t + 1)) for t, flujo in enumerate(flujos) if t > 0
    )


def calcular_tir(
    flujos: Sequence[float],
    estimacion_inicial: float = 0.10,
    tolerancia: float = 1e-7,
    max_iteraciones: int = 200,
) -> ResultadoTIR:
    """
    Calcula la TIR como la tasa r tal que VAN(r) = 0, usando Newton-Raphson
    y, si no converge, hace un barrido por bisección entre -0.99 y 10.0
    para encontrar un cambio de signo.
    """
    if not flujos or len(flujos) < 2:
        raise FinanceEngineError("Se necesitan al menos dos flujos (inversión y un retorno).")

    tasa = estimacion_inicial
    for i in range(max_iteraciones):
        van = _van_de(flujos, tasa)
        derivada = _van_derivada(flujos, tasa)
        if abs(derivada) < 1e-12:
            break
        nueva_tasa = tasa - van / derivada
        if abs(nueva_tasa - tasa) < tolerancia:
            return ResultadoTIR(valor=nueva_tasa, iteraciones=i + 1, convergio=True)
        tasa = nueva_tasa
        if tasa <= -0.999:
            tasa = -0.99  # evitar división por cero / explosión numérica

    # Respaldo: bisección buscando cambio de signo en VAN(r)
    lo, hi = -0.99, 10.0
    van_lo, van_hi = _van_de(flujos, lo), _van_de(flujos, hi)
    if van_lo * van_hi > 0:
        # No hay cambio de signo en el rango razonable -> no existe TIR real útil
        return ResultadoTIR(valor=None, iteraciones=max_iteraciones, convergio=False)

    for i in range(max_iteraciones):
        mid = (lo + hi) / 2
        van_mid = _van_de(flujos, mid)
        if abs(van_mid) < tolerancia:
            return ResultadoTIR(valor=mid, iteraciones=i + 1, convergio=True)
        if van_lo * van_mid < 0:
            hi = mid
        else:
            lo, van_lo = mid, van_mid

    return ResultadoTIR(valor=(lo + hi) / 2, iteraciones=max_iteraciones, convergio=True)


def interpretar_tir(resultado: ResultadoTIR, tasa_corte: float | None = None) -> ResultadoTIR:
    if not resultado.convergio or resultado.valor is None:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            "No fue posible encontrar una TIR real con los flujos ingresados (puede ocurrir "
            "cuando hay múltiples o ningún cambio de signo en el flujo de caja). Revisa los "
            "datos o usa el VAN como criterio principal en este caso."
        )
        return resultado

    pct = resultado.valor * 100
    if tasa_corte is None:
        resultado.semaforo = "neutro"
        resultado.interpretacion = (
            f"La TIR del proyecto es {pct:.2f}%. Esta es la rentabilidad anual implícita del "
            "proyecto. Para decidir si conviene aceptarlo, compárala con tu tasa de corte "
            "(costo de oportunidad del capital)."
        )
    elif resultado.valor > tasa_corte:
        resultado.semaforo = "positivo"
        resultado.interpretacion = (
            f"La TIR ({pct:.2f}%) es mayor que la tasa de corte ({tasa_corte * 100:.2f}%). "
            "El proyecto rinde más de lo que cuesta financiarlo: conviene aceptarlo (criterio "
            "consistente con un VAN positivo, salvo en flujos con múltiples cambios de signo)."
        )
    elif resultado.valor < tasa_corte:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            f"La TIR ({pct:.2f}%) es menor que la tasa de corte ({tasa_corte * 100:.2f}%). "
            "El proyecto no alcanza a cubrir el costo de oportunidad del capital: conviene "
            "rechazarlo."
        )
    else:
        resultado.semaforo = "neutro"
        resultado.interpretacion = (
            f"La TIR ({pct:.2f}%) es igual a la tasa de corte. Es el punto de indiferencia."
        )
    return resultado


# ---------------------------------------------------------------------------
# Payback (período de recuperación simple, no descontado)
# ---------------------------------------------------------------------------
def calcular_payback(flujos: Sequence[float]) -> ResultadoPayback:
    if not flujos:
        raise FinanceEngineError("Debe ingresar al menos un flujo de caja.")

    acumulado = []
    suma = 0.0
    for flujo in flujos:
        suma += flujo
        acumulado.append(suma)

    periodo = None
    for t, valor_acum in enumerate(acumulado):
        if valor_acum >= 0:
            if t == 0:
                periodo = 0.0
            else:
                anterior = acumulado[t - 1]
                fraccion = -anterior / (valor_acum - anterior) if valor_acum != anterior else 0
                periodo = (t - 1) + fraccion
            break

    return ResultadoPayback(periodo=periodo, flujo_acumulado=acumulado)


def interpretar_payback(resultado: ResultadoPayback, periodo_maximo_aceptable: float | None = None) -> ResultadoPayback:
    if resultado.periodo is None:
        resultado.semaforo = "negativo"
        resultado.interpretacion = (
            "Con los flujos ingresados, la inversión nunca se recupera dentro del horizonte "
            "evaluado. Este criterio por sí solo desaconseja el proyecto, aunque conviene "
            "revisarlo junto al VAN y la TIR, ya que el Payback ignora lo que ocurre después "
            "de recuperarse la inversión y no considera el valor del dinero en el tiempo."
        )
        return resultado

    base = (
        f"El período de recuperación (Payback) es de {resultado.periodo:.2f} años. "
        "Recuerda que este criterio es solo informativo: no descuenta los flujos futuros "
        "ni considera lo que sucede después del punto de recuperación, por lo que no debería "
        "usarse como criterio único de decisión."
    )
    if periodo_maximo_aceptable is not None:
        if resultado.periodo <= periodo_maximo_aceptable:
            resultado.semaforo = "positivo"
            base += (
                f" Como {resultado.periodo:.2f} años es menor o igual al máximo aceptable "
                f"definido ({periodo_maximo_aceptable:.2f} años), el proyecto cumple este criterio."
            )
        else:
            resultado.semaforo = "negativo"
            base += (
                f" Como {resultado.periodo:.2f} años supera el máximo aceptable definido "
                f"({periodo_maximo_aceptable:.2f} años), el proyecto no cumple este criterio."
            )
    else:
        resultado.semaforo = "neutro"
    resultado.interpretacion = base
    return resultado


# ---------------------------------------------------------------------------
# Tasa de Fisher: tasa de descuento donde dos proyectos tienen el mismo VAN
# ---------------------------------------------------------------------------
def calcular_tasa_fisher(
    flujos_a: Sequence[float],
    flujos_b: Sequence[float],
    tolerancia: float = 1e-7,
    max_iteraciones: int = 200,
) -> ResultadoTIR:
    """
    La tasa de Fisher es la TIR del flujo diferencial (A - B).
    Se reutiliza el mismo motor de cálculo de TIR.
    """
    n = max(len(flujos_a), len(flujos_b))
    a = list(flujos_a) + [0.0] * (n - len(flujos_a))
    b = list(flujos_b) + [0.0] * (n - len(flujos_b))
    diferencial = [x - y for x, y in zip(a, b)]
    return calcular_tir(diferencial, tolerancia=tolerancia, max_iteraciones=max_iteraciones)


def interpretar_tasa_fisher(resultado: ResultadoTIR, nombre_a: str = "A", nombre_b: str = "B") -> ResultadoTIR:
    if not resultado.convergio or resultado.valor is None:
        resultado.semaforo = "neutro"
        resultado.interpretacion = (
            "No existe un cruce de Fisher claro entre ambos proyectos en el flujo diferencial "
            "calculado: probablemente uno domina al otro en todo el rango de tasas razonable."
        )
        return resultado

    pct = resultado.valor * 100
    resultado.semaforo = "neutro"
    resultado.interpretacion = (
        f"La tasa de Fisher es {pct:.2f}%. Es el punto donde el VAN de '{nombre_a}' y "
        f"'{nombre_b}' se igualan. Por debajo de esta tasa de descuento conviene el proyecto "
        f"con mayor VAN a tasas bajas (típicamente el de mayor inversión); por encima, conviene "
        "el otro. Compara esta tasa con tu costo de capital real para saber cuál ranking aplica "
        "a tu caso."
    )
    return resultado


# ---------------------------------------------------------------------------
# IVAN (Índice de Valor Actual Neto) — para ranking de proyectos independientes
# con restricción de presupuesto.
# ---------------------------------------------------------------------------
def calcular_ivan(van: float, inversion_inicial: float) -> float:
    """
    IVAN = VAN / |Inversión inicial|
    Permite comparar "rentabilidad por peso invertido" entre proyectos
    independientes cuando hay racionamiento de capital.
    """
    if inversion_inicial == 0:
        raise FinanceEngineError("La inversión inicial no puede ser cero para calcular el IVAN.")
    return van / abs(inversion_inicial)


def interpretar_ivan(ivan: float) -> dict:
    if ivan > 0:
        semaforo = "positivo"
        texto = (
            f"El IVAN es {ivan:.4f}, es decir, por cada peso invertido el proyecto genera "
            f"{ivan:.4f} pesos de VAN adicional. Útil para rankear proyectos independientes "
            "cuando el presupuesto de inversión es limitado: prioriza los de mayor IVAN hasta "
            "agotar el presupuesto disponible."
        )
    else:
        semaforo = "negativo"
        texto = (
            f"El IVAN es {ivan:.4f} (negativo o cero): el proyecto no genera valor por peso "
            "invertido y no debería priorizarse en un ranking de capital racionado."
        )
    return {"valor": ivan, "semaforo": semaforo, "interpretacion": texto}
