"""Evaluación automatizada de calidad de los datos crudos (data/raw).

Pregunta de negocio que responde: ¿los datos de origen están dentro de las
tolerancias acordadas para poder ser preparados y usados en el modelo?

Cada regla se ejecuta como un caso de prueba independiente
(``test_regla_calidad_raw[<regla>]``) y compara el indicador con el umbral de
``params.yaml``. Ejecutar con:

    pytest tests/test_calidad_raw.py -v
"""

import warnings

import pytest

from src.calidad import reglas_raw
from src.utils import cargar_params, leer_raw

_P = cargar_params()
_RESULTADOS = {r.regla: r for r in reglas_raw(*leer_raw(_P), _P)}


@pytest.mark.parametrize("regla", list(_RESULTADOS))
def test_regla_calidad_raw(regla):
    r = _RESULTADOS[regla]
    signo = ">=" if r.tipo == "min" else "<="
    assert r.cumple, (f"[{r.dimension}] {r.descripcion}: {r.errores}/{r.total} = {r.valor:.4f}, "
                      f"se esperaba {signo} {r.umbral}")
    # Dentro de la tolerancia, pero con errores: se emite una advertencia para que
    # el hallazgo quede visible en el resumen de PyTest y se trate en la preparación.
    if r.tipo == "max" and r.errores > 0:
        warnings.warn(f"[{r.dimension}] {regla}: {r.errores} casos ({r.valor:.2%}) - {r.descripcion}",
                      UserWarning)


# --- Tests de esquema (estructura esperada según el diccionario de datos) ---

def test_esquema_clientes(clientes):
    esperadas = ["id_cliente", "edad", "genero", "ciudad", "antiguedad_cliente_meses", "canal_registro"]
    assert list(clientes.columns) == esperadas


def test_esquema_resenas(resenas):
    esperadas = ["id_resena", "id_cliente", "categoria_producto", "canal_compra", "plataforma",
                 "calificacion", "texto_resena", "tiempo_respuesta_horas", "problema_resuelto",
                 "reclamo_formal", "importe_compra", "fecha_resena", "sentimiento"]
    assert list(resenas.columns) == esperadas


def test_tipos_numericos(clientes, resenas):
    import pandas.api.types as t
    assert t.is_integer_dtype(clientes["id_cliente"])
    assert t.is_numeric_dtype(clientes["edad"])
    assert t.is_integer_dtype(resenas["calificacion"])
    assert t.is_float_dtype(resenas["importe_compra"])
