"""Fixtures compartidas por los tests de calidad y de preparación."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import cargar_params, leer_procesado, leer_raw  # noqa: E402


@pytest.fixture(scope="session")
def params():
    return cargar_params()


@pytest.fixture(scope="session")
def datos_raw(params):
    return leer_raw(params)


@pytest.fixture(scope="session")
def clientes(datos_raw):
    return datos_raw[0]


@pytest.fixture(scope="session")
def resenas(datos_raw):
    return datos_raw[1]


@pytest.fixture(scope="session")
def procesado(params):
    try:
        return leer_procesado(params)
    except FileNotFoundError:
        pytest.skip("No existe data/processed/datos_integrados.csv: ejecutar `dvc repro preparar`")
