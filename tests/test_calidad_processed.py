"""Evaluación de calidad del dataset preparado (data/processed).

Actúa como "quality gate": si alguno de estos tests falla, el dataset no se
considera apto para la fase de Modelado (AP2).

    pytest tests/test_calidad_processed.py -v
"""

import pytest

from src.calidad import reglas_processed


@pytest.fixture(scope="module")
def resultados(procesado, resenas, params):
    return {r.regla: r for r in reglas_processed(procesado, resenas, params)}


REGLAS = ["nulos", "duplicados", "rango_edad", "rango_tiempo_respuesta",
          "dominio_categoricos", "retencion_filas", "distribucion_clases"]


@pytest.mark.parametrize("regla", REGLAS)
def test_regla_calidad_processed(resultados, regla):
    r = resultados[regla]
    assert r.cumple, f"[{r.dimension}] {r.descripcion}: valor {r.valor:.4f}, umbral {r.umbral}"


def test_sin_fuga_de_informacion(procesado, params):
    """Las columnas que determinan el target o identifican filas no deben llegar al modelo."""
    prohibidas = set(params["preparacion"]["columnas_eliminar_final"])
    assert prohibidas.isdisjoint(procesado.columns)


def test_columnas_minimas_para_modelado(procesado):
    requeridas = {"texto_resena", "categoria_producto", "canal_compra", "plataforma",
                  "tiempo_respuesta_horas", "problema_resuelto", "reclamo_formal",
                  "importe_compra", "edad", "genero", "ciudad", "antiguedad_cliente_meses",
                  "longitud_resena", "cantidad_palabras_resena", "tiempo_respuesta_dias",
                  "sentimiento"}
    assert requeridas.issubset(procesado.columns)


def test_target_es_ultima_columna(procesado):
    assert procesado.columns[-1] == "sentimiento"


def test_atributos_derivados_coherentes(procesado):
    assert (procesado["longitud_resena"] == procesado["texto_resena"].str.len()).all()
    assert (procesado["tiempo_respuesta_dias"] * 24 - procesado["tiempo_respuesta_horas"]).abs().max() < 1e-6
    assert (procesado["resenas_previas_cliente"] >= 0).all()
