"""Utilidades comunes: lectura de parámetros y de los datasets del escenario."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]


def cargar_params(ruta: str | Path = RAIZ / "params.yaml") -> dict:
    """Lee params.yaml (fuente única de rutas, dominios y umbrales)."""
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ruta(rel: str) -> Path:
    """Convierte una ruta relativa a la raíz del repositorio en absoluta."""
    return RAIZ / rel


def leer_raw(params: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (clientes, resenas) tal como vienen en data/raw."""
    sep = params["lectura"]["separador"]
    clientes = pd.read_csv(ruta(params["rutas"]["clientes_raw"]), sep=sep)
    resenas = pd.read_csv(ruta(params["rutas"]["resenas_raw"]), sep=sep)
    return clientes, resenas


def leer_procesado(params: dict) -> pd.DataFrame:
    return pd.read_csv(ruta(params["rutas"]["dataset_procesado"]))


def guardar_json(datos: dict, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
