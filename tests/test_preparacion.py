"""Tests unitarios de los pasos de preparación con datos sintéticos mínimos.

No dependen de los CSV del proyecto: validan que cada transformación hace lo
que promete, para detectar regresiones al modificar src/preparacion.py.
"""

import numpy as np
import pandas as pd

from src.preparacion import (construir_atributos, eliminar_duplicados, imputar_mediana_por_grupo,
                             integrar, tratar_edad_fuera_de_rango)


def test_eliminar_duplicados_quita_filas_e_ids_repetidos():
    df = pd.DataFrame({"id_resena": [1, 1, 2, 2], "x": ["a", "a", "b", "c"]})
    out = eliminar_duplicados(df)
    assert out["id_resena"].is_unique and len(out) == 2


def test_edad_fuera_de_rango_se_imputa_sin_perder_clientes():
    df = pd.DataFrame({"id_cliente": [1, 2, 3], "edad": [30.0, 113.0, np.nan]})
    out = tratar_edad_fuera_de_rango(df, [18, 90], "imputar")
    assert len(out) == 3 and np.isnan(out.loc[1, "edad"])


def test_edad_fuera_de_rango_modo_eliminar():
    df = pd.DataFrame({"id_cliente": [1, 2], "edad": [30.0, 113.0]})
    assert len(tratar_edad_fuera_de_rango(df, [18, 90], "eliminar")) == 1


def test_imputacion_por_mediana_de_grupo():
    df = pd.DataFrame({"g": ["a", "a", "a", "b", "b"], "v": [1.0, 3.0, np.nan, 10.0, np.nan]})
    out, medianas = imputar_mediana_por_grupo(df, "v", "g")
    assert out["v"].tolist() == [1.0, 3.0, 2.0, 10.0, 10.0]
    assert medianas == {"a": 2.0, "b": 10.0}


def test_integracion_conserva_todas_las_resenas():
    r = pd.DataFrame({"id_resena": [1, 2, 3], "id_cliente": [1, 1, 2]})
    c = pd.DataFrame({"id_cliente": [1, 2], "edad": [30, 40]})
    assert len(integrar(r, c)) == 3


def test_resenas_previas_usa_solo_el_pasado():
    df = pd.DataFrame({
        "id_resena": [10, 11, 12],
        "id_cliente": [7, 7, 7],
        "fecha_resena": ["2025-03-01", "2025-01-01", "2025-02-01"],
        "texto_resena": ["a b", "c", "d e f"],
        "tiempo_respuesta_horas": [24.0, 12.0, 6.0],
    })
    out = construir_atributos(df, {"resenas_previas_cliente": True, "cantidad_palabras_resena": True,
                                   "tiempo_respuesta_dias": True})
    assert out["resenas_previas_cliente"].tolist() == [2, 0, 1]
    assert out["cantidad_palabras_resena"].tolist() == [2, 1, 3]
    assert out["tiempo_respuesta_dias"].tolist() == [1.0, 0.5, 0.25]
