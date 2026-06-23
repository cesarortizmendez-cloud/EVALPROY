"""
finance_engine
==============
Motor financiero puro (sin dependencias de Django) que centraliza TODOS los
cálculos de evaluación de proyectos de inversión usados por las apps del
sitio. Se puede importar y testear de forma independiente:

    from apps.finance_engine import calcular_van, interpretar_van

Organizado en submódulos por tema:
    - evaluacion:       VAN, TIR, Payback, Fisher, IVAN
    - depreciacion:     lineal y acelerada
    - tasa_descuento:   CAPM, beta, WACC
    - riesgo:           sensibilidad, escenarios, árboles de decisión, opciones reales
    - reemplazo:        CAUE para reemplazo de equipos
"""
from .evaluacion import (
    FinanceEngineError,
    calcular_van, interpretar_van, ResultadoVAN,
    calcular_tir, interpretar_tir, ResultadoTIR,
    calcular_payback, interpretar_payback, ResultadoPayback,
    calcular_tasa_fisher, interpretar_tasa_fisher,
    calcular_ivan, interpretar_ivan,
)
from .no_periodicos import (
    calcular_van_no_periodico, interpretar_van_no_periodico, ResultadoVanNoPeriodico,
    calcular_tir_no_periodico, interpretar_tir_no_periodico, ResultadoTirNoPeriodico,
)
from .depreciacion import (
    depreciacion_lineal, depreciacion_acelerada_suma_digitos,
    comparar_metodos_depreciacion, ResultadoDepreciacion,
)
from .tasa_descuento import (
    costo_patrimonio_capm, ResultadoCAPM,
    desapalancar_beta, apalancar_beta,
    calcular_wacc, ResultadoWACC,
)
from .riesgo import (
    analisis_sensibilidad_univariado, construir_tornado, ResultadoSensibilidad,
    Escenario, analisis_escenarios, ResultadoEscenarios,
    NodoDecision, evaluar_arbol_decision,
    opcion_real_black_scholes, ResultadoOpcionReal,
)
from .reemplazo import (
    factor_recuperacion_capital, calcular_caue, comparar_caue_alternativas, ResultadoCAUE,
    calcular_vida_economica, ResultadoVidaEconomica, FilaTanteo, FilaCAE,
    calcular_momento_optimo_reemplazo, ResultadoMomentoOptimo,
)

__all__ = [
    "FinanceEngineError",
    "calcular_van", "interpretar_van", "ResultadoVAN",
    "calcular_tir", "interpretar_tir", "ResultadoTIR",
    "calcular_payback", "interpretar_payback", "ResultadoPayback",
    "calcular_tasa_fisher", "interpretar_tasa_fisher",
    "calcular_ivan", "interpretar_ivan",
    "calcular_van_no_periodico", "interpretar_van_no_periodico", "ResultadoVanNoPeriodico",
    "calcular_tir_no_periodico", "interpretar_tir_no_periodico", "ResultadoTirNoPeriodico",
    "depreciacion_lineal", "depreciacion_acelerada_suma_digitos",
    "comparar_metodos_depreciacion", "ResultadoDepreciacion",
    "costo_patrimonio_capm", "ResultadoCAPM",
    "desapalancar_beta", "apalancar_beta",
    "calcular_wacc", "ResultadoWACC",
    "analisis_sensibilidad_univariado", "construir_tornado", "ResultadoSensibilidad",
    "Escenario", "analisis_escenarios", "ResultadoEscenarios",
    "NodoDecision", "evaluar_arbol_decision",
    "opcion_real_black_scholes", "ResultadoOpcionReal",
    "factor_recuperacion_capital", "calcular_caue", "comparar_caue_alternativas", "ResultadoCAUE",
    "calcular_vida_economica", "ResultadoVidaEconomica", "FilaTanteo", "FilaCAE",
    "calcular_momento_optimo_reemplazo", "ResultadoMomentoOptimo",
]
