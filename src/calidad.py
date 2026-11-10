"""Reglas de calidad de datos (DMBoK cap. 13 + ISO/IEC 25012).

Cada regla devuelve un ``Resultado`` con el indicador calculado como
``errores / total`` (o una proporción mínima exigida) y lo compara con el
umbral de aceptación definido en ``params.yaml``. Las mismas funciones las
usan los tests de PyTest (tests/) y el generador de reportes
(src/reporte_calidad.py), de modo que la definición de cada regla existe en
un único lugar.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass
class Resultado:
    regla: str
    dimension: str          # característica ISO/IEC 25012
    descripcion: str
    errores: int
    total: int
    valor: float            # proporción calculada
    umbral: float
    tipo: str = "max"       # "max": valor <= umbral ; "min": valor >= umbral

    @property
    def cumple(self) -> bool:
        if self.tipo == "min":
            return self.valor >= self.umbral
        return self.valor <= self.umbral

    def a_dict(self) -> dict:
        d = asdict(self)
        d["valor"] = round(self.valor, 6)
        d["cumple"] = self.cumple
        return d


def _ratio(errores: int, total: int) -> float:
    return errores / total if total else 0.0


def _fuera_de_rango(serie: pd.Series, minimo, maximo) -> pd.Series:
    """True donde el valor existe y está fuera de [minimo, maximo]."""
    return serie.notna() & ((serie < minimo) | (serie > maximo))


# ---------------------------------------------------------------------------
# Reglas sobre los datos crudos (data/raw)
# ---------------------------------------------------------------------------

def reglas_raw(clientes: pd.DataFrame, resenas: pd.DataFrame, p: dict) -> list[Resultado]:
    u = p["calidad"]["raw"]
    rg = p["rangos"]
    dom = p["dominios"]
    nc, nr = len(clientes), len(resenas)
    out: list[Resultado] = []

    # --- Completitud -------------------------------------------------------
    e = int(clientes["edad"].isna().sum())
    out.append(Resultado("completitud_edad", "Completitud",
                         "Clientes sin edad informada", e, nc, _ratio(e, nc), u["completitud_edad"]))

    e = int(resenas["tiempo_respuesta_horas"].isna().sum())
    out.append(Resultado("completitud_tiempo_respuesta", "Completitud",
                         "Reseñas sin tiempo de respuesta", e, nr, _ratio(e, nr),
                         u["completitud_tiempo_respuesta"]))

    opc = {"edad", "tiempo_respuesta_horas"}
    celdas_c = clientes.drop(columns=[c for c in opc if c in clientes]).isna().sum().sum()
    celdas_r = resenas.drop(columns=[c for c in opc if c in resenas]).isna().sum().sum()
    tot = clientes.drop(columns=["edad"]).size + resenas.drop(columns=["tiempo_respuesta_horas"]).size
    e = int(celdas_c + celdas_r)
    out.append(Resultado("completitud_obligatorios", "Completitud",
                         "Celdas vacías en campos obligatorios", e, tot, _ratio(e, tot),
                         u["completitud_obligatorios"]))

    # --- Unicidad (DMBoK) / Consistencia -----------------------------------
    e = int(clientes["id_cliente"].duplicated().sum())
    out.append(Resultado("unicidad_id_cliente", "Consistencia",
                         "id_cliente repetidos", e, nc, _ratio(e, nc), u["unicidad_id_cliente"]))

    e = int(resenas["id_resena"].duplicated().sum())
    out.append(Resultado("unicidad_id_resena", "Consistencia",
                         "id_resena repetidos", e, nr, _ratio(e, nr), u["unicidad_id_resena"]))

    e = int(resenas.duplicated().sum())
    out.append(Resultado("duplicados_resenas", "Consistencia",
                         "Filas de reseñas completamente duplicadas", e, nr, _ratio(e, nr),
                         u["duplicados_resenas"]))

    # --- Exactitud semántica: rangos válidos -------------------------------
    e = int(_fuera_de_rango(clientes["edad"], *rg["edad"]).sum())
    out.append(Resultado("rango_edad", "Exactitud",
                         f"Edad fuera de {rg['edad']}", e, nc, _ratio(e, nc), u["rango_edad"]))

    e = int(_fuera_de_rango(resenas["calificacion"], *rg["calificacion"]).sum())
    out.append(Resultado("rango_calificacion", "Exactitud",
                         f"Calificación fuera de {rg['calificacion']}", e, nr, _ratio(e, nr),
                         u["rango_calificacion"]))

    e = int(_fuera_de_rango(clientes["antiguedad_cliente_meses"], *rg["antiguedad_cliente_meses"]).sum())
    out.append(Resultado("rango_antiguedad", "Exactitud",
                         f"Antigüedad fuera de {rg['antiguedad_cliente_meses']} meses", e, nc,
                         _ratio(e, nc), u["rango_antiguedad"]))

    e = int(_fuera_de_rango(resenas["tiempo_respuesta_horas"], *rg["tiempo_respuesta_horas"]).sum())
    out.append(Resultado("rango_tiempo_respuesta", "Exactitud",
                         f"Tiempo de respuesta fuera de {rg['tiempo_respuesta_horas']} h", e, nr,
                         _ratio(e, nr), u["rango_tiempo_respuesta"]))

    e = int((resenas["importe_compra"] <= rg["importe_compra_min"]).sum())
    out.append(Resultado("importe_positivo", "Exactitud",
                         "Importe de compra no positivo", e, nr, _ratio(e, nr), u["importe_positivo"]))

    # --- Exactitud sintáctica: dominios y formatos -------------------------
    e, tot = 0, 0
    for df in (clientes, resenas):
        for col, valores in dom.items():
            if col in df:
                e += int((~df[col].isin(valores)).sum())
                tot += len(df)
    out.append(Resultado("dominio_categoricos", "Exactitud",
                         "Valores categóricos fuera del dominio del diccionario", e, tot,
                         _ratio(e, tot), u["dominio_categoricos"]))

    fechas = pd.to_datetime(resenas["fecha_resena"], format="%Y-%m-%d", errors="coerce")
    e = int(fechas.isna().sum())
    out.append(Resultado("formato_fecha", "Conformidad",
                         "Fechas que no cumplen el formato ISO YYYY-MM-DD", e, nr, _ratio(e, nr),
                         u["formato_fecha"]))

    ini, fin = (pd.Timestamp(x) for x in rg["fecha_resena"])
    e = int((fechas.notna() & ((fechas < ini) | (fechas > fin))).sum())
    out.append(Resultado("actualidad_fecha", "Actualidad",
                         f"Fechas fuera de la ventana {rg['fecha_resena']}", e, nr, _ratio(e, nr),
                         u["actualidad_fecha"]))

    e = int((resenas["texto_resena"].fillna("").str.strip().str.len() < rg["longitud_texto_min"]).sum())
    out.append(Resultado("longitud_texto", "Exactitud",
                         f"Reseñas con menos de {rg['longitud_texto_min']} caracteres", e, nr,
                         _ratio(e, nr), u["longitud_texto"]))

    # --- Consistencia: integridad referencial y coherencia entre atributos -
    e = int((~resenas["id_cliente"].isin(clientes["id_cliente"])).sum())
    out.append(Resultado("integridad_referencial", "Consistencia",
                         "Reseñas cuyo id_cliente no existe en clientes", e, nr, _ratio(e, nr),
                         u["integridad_referencial"]))

    esperado = resenas["calificacion"].map(
        lambda c: "Negativo" if c <= 2 else ("Neutral" if c == 3 else "Positivo"))
    e = int((esperado != resenas["sentimiento"]).sum())
    out.append(Resultado("coherencia_calificacion_sentimiento", "Consistencia",
                         "Sentimiento distinto al esperado por la calificación "
                         "(1-2 Negativo, 3 Neutral, 4-5 Positivo)", e, nr, _ratio(e, nr),
                         u["coherencia_calificacion_sentimiento"]))

    con_edad = clientes.dropna(subset=["edad"])
    edad_registro = con_edad["edad"] - con_edad["antiguedad_cliente_meses"] / 12
    e = int((edad_registro < rg["edad_minima_registro"]).sum())
    out.append(Resultado("coherencia_edad_antiguedad", "Consistencia",
                         f"Clientes que se habrían registrado con menos de "
                         f"{rg['edad_minima_registro']} años", e, len(con_edad),
                         _ratio(e, len(con_edad)), u["coherencia_edad_antiguedad"]))

    # --- Adecuación al uso: balance de la variable objetivo ----------------
    props = resenas["sentimiento"].value_counts(normalize=True)
    out.append(Resultado("balance_clase_minoritaria", "Adecuación al uso",
                         f"Proporción de la clase minoritaria ({props.idxmin()})",
                         int(props.min() * nr), nr, float(props.min()),
                         u["balance_clase_minoritaria"], tipo="min"))
    return out


# ---------------------------------------------------------------------------
# Reglas sobre el dataset preparado (data/processed)
# ---------------------------------------------------------------------------

def reglas_processed(df: pd.DataFrame, resenas_raw: pd.DataFrame, p: dict) -> list[Resultado]:
    u = p["calidad"]["processed"]
    rg = p["rangos"]
    n = len(df)
    out: list[Resultado] = []

    e = int(df.isna().sum().sum())
    out.append(Resultado("nulos", "Completitud", "Celdas nulas en el dataset final",
                         e, df.size, _ratio(e, df.size), u["nulos"]))

    e = int(df.duplicated().sum())
    out.append(Resultado("duplicados", "Consistencia", "Filas duplicadas en el dataset final",
                         e, n, _ratio(e, n), u["duplicados"]))

    e = int(_fuera_de_rango(df["edad"], *rg["edad"]).sum())
    out.append(Resultado("rango_edad", "Exactitud", f"Edad fuera de {rg['edad']}",
                         e, n, _ratio(e, n), u["rango_edad"]))

    e = int(_fuera_de_rango(df["tiempo_respuesta_horas"], *rg["tiempo_respuesta_horas"]).sum())
    out.append(Resultado("rango_tiempo_respuesta", "Exactitud", "Tiempo de respuesta fuera de rango",
                         e, n, _ratio(e, n), u["rango_tiempo_respuesta"]))

    e, tot = 0, 0
    for col, valores in p["dominios"].items():
        if col in df:
            e += int((~df[col].isin(valores)).sum())
            tot += n
    out.append(Resultado("dominio_categoricos", "Exactitud", "Categóricos fuera de dominio",
                         e, tot, _ratio(e, tot), u["dominio_categoricos"]))

    unicas = int((~resenas_raw.duplicated()).sum())
    out.append(Resultado("retencion_filas", "Completitud",
                         "Filas finales / reseñas únicas de origen", n, unicas,
                         _ratio(n, unicas), u["retencion_filas_min"], tipo="min"))

    antes = resenas_raw.drop_duplicates()["sentimiento"].value_counts(normalize=True)
    despues = df["sentimiento"].value_counts(normalize=True)
    desvio = float((antes - despues).abs().max())
    out.append(Resultado("distribucion_clases", "Adecuación al uso",
                         "Máximo desvío de proporción de clases respecto al origen",
                         0, n, desvio, u["desvio_distribucion_clases_max"]))
    return out


def a_tabla(resultados: list[Resultado]) -> pd.DataFrame:
    return pd.DataFrame([r.a_dict() for r in resultados])
