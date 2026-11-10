"""Preparación de los datos (migrado y ampliado desde CD02_Procesamiento.ipynb).

Uso:
    python -m src.preparacion

Entrada : data/raw/datos_clientes.csv, data/raw/datos_resenas.csv
Salida  : data/processed/datos_integrados.csv
          reports/preparacion/resumen_preparacion.json (trazabilidad)

Cada paso es una función pura (DataFrame -> DataFrame) para poder probarla
de forma aislada (tests/test_preparacion.py) y reutilizarla en producción.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils import cargar_params, guardar_json, leer_raw, ruta

# ---------------------------------------------------------------------------
# Pasos de transformación
# ---------------------------------------------------------------------------


def seleccionar_columnas(df: pd.DataFrame, eliminar: list[str]) -> pd.DataFrame:
    """Selección de atributos: descarta columnas sin valor para el objetivo."""
    return df.drop(columns=[c for c in eliminar if c in df.columns])


def eliminar_duplicados(resenas: pd.DataFrame) -> pd.DataFrame:
    """Quita filas repetidas y garantiza unicidad de id_resena."""
    return resenas.drop_duplicates().drop_duplicates(subset="id_resena", keep="first")


def tratar_edad_fuera_de_rango(clientes: pd.DataFrame, rango: list, modo: str) -> pd.DataFrame:
    """Edades fuera de rango -> NaN (para imputar) o se elimina el cliente.

    Con ``modo='imputar'`` (por defecto) se conserva al cliente y, por lo tanto,
    todas sus reseñas. El MVP eliminaba al cliente y perdía sus reseñas en el
    ``merge`` interno.
    """
    df = clientes.copy()
    fuera = df["edad"].notna() & ((df["edad"] < rango[0]) | (df["edad"] > rango[1]))
    if modo == "eliminar":
        return df[~fuera]
    df.loc[fuera, "edad"] = np.nan
    return df


def imputar_mediana_por_grupo(df: pd.DataFrame, col: str, grupo: str) -> tuple[pd.DataFrame, dict]:
    """Imputa nulos con la mediana del grupo y devuelve los valores usados."""
    df = df.copy()
    medianas = df.groupby(grupo)[col].median()
    df[col] = df[col].fillna(df[grupo].map(medianas))
    df[col] = df[col].fillna(df[col].median())  # respaldo si un grupo es todo nulo
    return df, {k: round(float(v), 3) for k, v in medianas.items()}


def integrar(resenas: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Une reseñas y clientes por id_cliente (cada reseña conserva su cliente)."""
    return resenas.merge(clientes, on="id_cliente", how="inner", validate="many_to_one")


def construir_atributos(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = df.copy()
    fecha = pd.to_datetime(df["fecha_resena"])
    if cfg.get("longitud_resena"):
        df["longitud_resena"] = df["texto_resena"].str.len()
    if cfg.get("cantidad_palabras_resena"):
        df["cantidad_palabras_resena"] = df["texto_resena"].str.split().str.len()
    if cfg.get("tiempo_respuesta_dias"):
        df["tiempo_respuesta_dias"] = df["tiempo_respuesta_horas"] / 24
    if cfg.get("resenas_previas_cliente"):
        # Reseñas anteriores del mismo cliente: solo usa información del pasado
        # (ordenada por fecha e id), evitando fuga de información futura.
        orden = df.assign(_f=fecha).sort_values(["id_cliente", "_f", "id_resena"])
        df["resenas_previas_cliente"] = orden.groupby("id_cliente").cumcount().reindex(df.index)
    if cfg.get("mes_resena"):
        df["mes_resena"] = fecha.dt.month
    if cfg.get("dia_semana_resena"):
        df["dia_semana_resena"] = fecha.dt.dayofweek
    return df


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------


def preparar(clientes: pd.DataFrame, resenas: pd.DataFrame, p: dict) -> tuple[pd.DataFrame, dict]:
    cfg = p["preparacion"]
    traza: dict = {"origen": {"clientes": len(clientes), "resenas": len(resenas)}}

    clientes = seleccionar_columnas(clientes, cfg["columnas_eliminar_clientes"])

    n = len(resenas)
    resenas = eliminar_duplicados(resenas)
    traza["duplicados_eliminados"] = n - len(resenas)

    fuera = int(((clientes["edad"] < p["rangos"]["edad"][0]) | (clientes["edad"] > p["rangos"]["edad"][1])).sum())
    clientes = tratar_edad_fuera_de_rango(clientes, p["rangos"]["edad"], cfg["edad_fuera_de_rango"])
    traza["edades_fuera_de_rango"] = {"cantidad": fuera, "tratamiento": cfg["edad_fuera_de_rango"]}

    traza["imputacion"] = {}
    for col, regla in cfg["imputacion"].items():
        objetivo = clientes if col in clientes else resenas
        nulos = int(objetivo[col].isna().sum())
        objetivo, medianas = imputar_mediana_por_grupo(objetivo, col, regla["agrupar_por"])
        if col in clientes:
            clientes = objetivo
        else:
            resenas = objetivo
        traza["imputacion"][col] = {"nulos_imputados": nulos, "agrupar_por": regla["agrupar_por"],
                                    "medianas": medianas}

    if cfg.get("filtrar_incoherencia_calificacion"):
        esperado = resenas["calificacion"].map(
            lambda c: "Negativo" if c <= 2 else ("Neutral" if c == 3 else "Positivo"))
        n = len(resenas)
        resenas = resenas[esperado == resenas["sentimiento"]]
        traza["filas_incoherentes_eliminadas"] = n - len(resenas)

    df = integrar(resenas, clientes)
    traza["filas_integradas"] = len(df)

    df = construir_atributos(df, cfg["nuevos_atributos"])
    df = seleccionar_columnas(df, cfg["columnas_eliminar_final"])

    # Formato final: columnas ordenadas, target al final, tipos explícitos
    target = "sentimiento"
    df = df[[c for c in df.columns if c != target] + [target]]
    df["edad"] = df["edad"].round().astype(int)
    df = df.reset_index(drop=True)

    traza["final"] = {"filas": len(df), "columnas": list(df.columns),
                      "distribucion_sentimiento": df[target].value_counts(normalize=True).round(4).to_dict()}
    return df, traza


def main() -> None:
    p = cargar_params()
    clientes, resenas = leer_raw(p)
    df, traza = preparar(clientes, resenas, p)

    salida = ruta(p["rutas"]["dataset_procesado"])
    salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida, index=False)
    guardar_json(traza, ruta(p["rutas"]["preparacion"]) / "resumen_preparacion.json")
    print(f"[preparacion] {traza['origen']['resenas']} reseñas -> {len(df)} filas x {df.shape[1]} columnas")


if __name__ == "__main__":
    main()
