"""
Tests del motor VAN.NO.PER / TIR.NO.PER, validados contra los valores
exactos obtenidos en Excel (apunte UNAB 'Técnicas de evaluación de
proyectos' y caso taller 2 de la Unidad 2).
"""
from datetime import date

import pytest

from apps.finance_engine.no_periodicos import (
    calcular_van_no_periodico, calcular_tir_no_periodico, FinanceEngineError,
)


def test_van_no_periodico_caso_apunte():
    fechas = [date(2021, 1, 1), date(2022, 12, 31), date(2024, 12, 31), date(2025, 12, 31)]
    flujos = [-10000, 3000, 11000, 5000]
    resultado = calcular_van_no_periodico(fechas, flujos, 0.11)
    assert resultado.valor == pytest.approx(2648.86, abs=0.05)


def test_tir_no_periodico_caso_apunte():
    fechas = [date(2021, 1, 1), date(2022, 12, 31), date(2024, 12, 31), date(2025, 12, 31)]
    flujos = [-10000, 3000, 11000, 5000]
    resultado = calcular_tir_no_periodico(fechas, flujos)
    assert resultado.convergio
    assert resultado.valor * 100 == pytest.approx(18.05, abs=0.05)


def test_van_no_periodico_caso_p3_taller():
    fechas = [date(2021, 1, 1), date(2023, 12, 31), date(2024, 12, 31), date(2025, 12, 31), date(2026, 1, 1)]
    flujos = [-330000, 120000, 120000, 120000, 120000]
    resultado = calcular_van_no_periodico(fechas, flujos, 0.10)
    assert resultado.valor == pytest.approx(-8855.40, abs=0.5)


def test_tir_no_periodico_caso_p3_taller():
    fechas = [date(2021, 1, 1), date(2023, 12, 31), date(2024, 12, 31), date(2025, 12, 31), date(2026, 1, 1)]
    flujos = [-330000, 120000, 120000, 120000, 120000]
    resultado = calcular_tir_no_periodico(fechas, flujos)
    assert resultado.valor * 100 == pytest.approx(9.2874, abs=0.01)


def test_van_no_periodico_caso_p4_taller():
    fechas = [date(2021, 1, 1), date(2023, 12, 31), date(2024, 12, 31), date(2025, 12, 31)]
    flujos = [-50000, 17000, 35000, 20000]
    resultado = calcular_van_no_periodico(fechas, flujos, 0.081)
    assert resultado.valor == pytest.approx(2640.41, abs=0.5)


def test_fechas_desordenadas_lanzan_error():
    fechas = [date(2022, 1, 1), date(2021, 1, 1)]
    flujos = [-1000, 1000]
    with pytest.raises(FinanceEngineError):
        calcular_van_no_periodico(fechas, flujos, 0.10)
