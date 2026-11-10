"""Genera el reporte de calidad de datos de una etapa del pipeline.

Uso:
    python -m src.reporte_calidad --etapa raw
    python -m src.reporte_calidad --etapa processed

Salidas (en reports/calidad/):
    metricas_<etapa>.json   -> métricas DVC (dvc metrics show / diff)
    reporte_<etapa>.md      -> tabla legible para la memoria y el repositorio

El reporte NO interrumpe el pipeline: la decisión de aceptar o rechazar los
datos la toman los tests de PyTest (tests/test_calidad_*.py).
"""

from __future__ import annotations

import argparse
from datetime import datetime

from src.calidad import a_tabla, reglas_processed, reglas_raw
from src.utils import cargar_params, guardar_json, leer_procesado, leer_raw, ruta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapa", choices=["raw", "processed"], required=True)
    etapa = ap.parse_args().etapa

    p = cargar_params()
    clientes, resenas = leer_raw(p)
    if etapa == "raw":
        resultados = reglas_raw(clientes, resenas, p)
    else:
        resultados = reglas_processed(leer_procesado(p), resenas, p)

    tabla = a_tabla(resultados)
    destino = ruta(p["rutas"]["calidad"])

    metricas = {
        "etapa": etapa,
        "reglas_evaluadas": len(tabla),
        "reglas_cumplidas": int(tabla["cumple"].sum()),
        "indice_calidad": round(float(tabla["cumple"].mean()), 4),
        "reglas": {r["regla"]: {"valor": r["valor"], "umbral": r["umbral"], "cumple": r["cumple"]}
                   for r in tabla.to_dict("records")},
    }
    guardar_json(metricas, destino / f"metricas_{etapa}.json")

    md = [f"# Reporte de calidad de datos – etapa `{etapa}`", "",
          f"Generado: {datetime.now():%Y-%m-%d %H:%M}  ",
          f"Reglas cumplidas: **{metricas['reglas_cumplidas']} / {metricas['reglas_evaluadas']}** "
          f"(índice {metricas['indice_calidad']:.0%})", "",
          "| Regla | Dimensión ISO 25012 | Descripción | Errores | Total | Valor | Umbral | Cumple |",
          "|---|---|---|---:|---:|---:|---:|:---:|"]
    for r in tabla.to_dict("records"):
        signo = "≥" if r["tipo"] == "min" else "≤"
        md.append(f"| {r['regla']} | {r['dimension']} | {r['descripcion']} | {r['errores']} | "
                  f"{r['total']} | {r['valor']:.4f} | {signo} {r['umbral']} | "
                  f"{'✅' if r['cumple'] else '❌'} |")
    (destino / f"reporte_{etapa}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"[calidad:{etapa}] {metricas['reglas_cumplidas']}/{metricas['reglas_evaluadas']} reglas cumplidas")
    for r in tabla[~tabla["cumple"]].to_dict("records"):
        print(f"  [X] {r['regla']}: {r['valor']:.4f} (umbral {r['umbral']})")


if __name__ == "__main__":
    main()
