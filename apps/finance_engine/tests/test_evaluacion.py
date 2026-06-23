"""
Tests del motor de evaluación de proyectos.
Ejecutar desde la raíz del proyecto con:
    pytest apps/finance_engine/tests -v
"""
import math
import pytest

from apps.finance_engine.evaluacion import (
    calcular_van, calcular_tir, calcular_payback,
    calcular_tasa_fisher, calcular_ivan, FinanceEngineError,
)
from apps.finance_engine.depreciacion import (
    depreciacion_lineal, depreciacion_acelerada_suma_digitos,
)
from apps.finance_engine.tasa_descuento import costo_patrimonio_capm, calcular_wacc
from apps.finance_engine.reemplazo import calcular_caue


def test_van_proyecto_simple():
    # Inversión 1000, retorno 600 por 3 años, tasa 10%
    flujos = [-1000, 600, 600, 600]
    resultado = calcular_van(flujos, 0.10)
    assert resultado.valor == pytest.approx(492.11, abs=0.5)


def test_van_flujo_vacio_lanza_error():
    with pytest.raises(FinanceEngineError):
        calcular_van([], 0.10)


def test_tir_proyecto_simple():
    flujos = [-1000, 600, 600, 600]
    resultado = calcular_tir(flujos)
    assert resultado.convergio
    # VAN debe ser ~0 a la TIR encontrada
    van_en_tir = calcular_van(flujos, resultado.valor).valor
    assert van_en_tir == pytest.approx(0, abs=1)


def test_payback_recupera_en_dos_anios():
    flujos = [-1000, 400, 600, 800]
    resultado = calcular_payback(flujos)
    assert resultado.periodo == pytest.approx(2.0, abs=0.01)


def test_payback_nunca_se_recupera():
    flujos = [-1000, 100, 100]
    resultado = calcular_payback(flujos)
    assert resultado.periodo is None


def test_ivan():
    ivan = calcular_ivan(van=500, inversion_inicial=-1000)
    assert ivan == pytest.approx(0.5)


def test_tasa_fisher_entre_dos_proyectos():
    a = [-1000, 0, 0, 1500]
    b = [-1000, 500, 500, 500]
    resultado = calcular_tasa_fisher(a, b)
    assert resultado.convergio


def test_depreciacion_lineal_suma_correcta():
    resultado = depreciacion_lineal(valor_activo=10000, valor_residual=1000, vida_util=5)
    assert sum(resultado.cuotas_anuales) == pytest.approx(9000)
    assert all(c == pytest.approx(1800) for c in resultado.cuotas_anuales)


def test_depreciacion_acelerada_suma_correcta_y_decrece():
    resultado = depreciacion_acelerada_suma_digitos(valor_activo=10000, valor_residual=1000, vida_util=5)
    assert sum(resultado.cuotas_anuales) == pytest.approx(9000)
    assert resultado.cuotas_anuales[0] > resultado.cuotas_anuales[-1]


def test_capm():
    resultado = costo_patrimonio_capm(tasa_libre_riesgo=0.04, beta=1.2, premio_riesgo_mercado=0.06)
    assert resultado.ke == pytest.approx(0.04 + 1.2 * 0.06)


def test_wacc():
    resultado = calcular_wacc(ke=0.15, kd=0.08, valor_patrimonio=600, valor_deuda=400, tasa_impuesto=0.27)
    esperado = 0.6 * 0.15 + 0.4 * 0.08 * (1 - 0.27)
    assert resultado.wacc == pytest.approx(esperado)


def test_caue_basico():
    resultado = calcular_caue(costos_anuales=[200, 200, 200], inversion_inicial=1000, valor_salvamento=200, tasa=0.10)
    assert resultado.caue > 0
