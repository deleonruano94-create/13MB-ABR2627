"""Exploración visual de los datos crudos (migrado desde CD01_Visualizacion.ipynb).

Uso:
    python -m src.visualizacion

Exporta los gráficos a reports/figures/ y un resumen descriptivo a
reports/figures/resumen_exploracion.json, sin depender de la libreta.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # sin interfaz gráfica: apto para ejecución automatizada

import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

from src.utils import cargar_params, guardar_json, leer_raw, ruta  # noqa: E402

ORDEN_SENT = ["Negativo", "Neutral", "Positivo"]


def _guardar(fig, destino, nombre, dpi):
    fig.tight_layout()
    fig.savefig(destino / f"{nombre}.png", dpi=dpi)
    plt.close(fig)


def main() -> None:
    p = cargar_params()
    dpi = p["visualizacion"]["dpi"]
    sns.set_theme(style=p["visualizacion"]["estilo"], palette="muted")
    destino = ruta(p["rutas"]["figuras"])
    destino.mkdir(parents=True, exist_ok=True)

    clientes, resenas = leer_raw(p)

    # 1. Distribución de la variable objetivo
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(x="sentimiento", data=resenas, order=ORDEN_SENT, ax=ax)
    ax.set(title="Distribución de la variable objetivo (sentimiento)",
           xlabel="Sentimiento", ylabel="Cantidad de reseñas")
    _guardar(fig, destino, "01_distribucion_sentimiento", dpi)

    # 2. Longitud del texto según sentimiento
    tmp = resenas.assign(longitud_texto=resenas["texto_resena"].str.len())
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(x="sentimiento", y="longitud_texto", data=tmp, order=ORDEN_SENT, ax=ax)
    ax.set(title="Longitud del texto de la reseña según sentimiento",
           xlabel="Sentimiento", ylabel="Caracteres")
    _guardar(fig, destino, "02_longitud_texto_sentimiento", dpi)

    # 3. Variables categóricas
    cat_cli = ["genero", "ciudad", "canal_registro"]
    cat_res = ["categoria_producto", "canal_compra", "plataforma", "problema_resuelto", "reclamo_formal"]
    for df, cols, pref in ((clientes, cat_cli, "03_clientes"), (resenas, cat_res, "04_resenas")):
        for col in cols:
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.countplot(y=col, data=df, order=df[col].value_counts().index, ax=ax)
            ax.set(title=f"Distribución de {col}", xlabel="Cantidad", ylabel=col)
            _guardar(fig, destino, f"{pref}_{col}", dpi)

    # 4. Correlaciones numéricas
    for df, nombre in ((clientes, "clientes"), (resenas, "resenas")):
        num = df.select_dtypes("number").drop(columns=[c for c in df if c.startswith("id_")])
        fig, ax = plt.subplots(figsize=(7, 5.5))
        sns.heatmap(num.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        ax.set_title(f"Matriz de correlaciones – {nombre}")
        _guardar(fig, destino, f"05_correlacion_{nombre}", dpi)

    # 5. (Nuevo) Gráficos orientados a calidad de datos
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(clientes["edad"].dropna(), bins=40, ax=ax)
    lim = p["rangos"]["edad"][1]
    ax.axvline(lim, color="crimson", ls="--", label=f"límite {lim} años")
    ax.set(title="Distribución de edad (con valores atípicos)", xlabel="Edad", ylabel="Clientes")
    ax.legend()
    _guardar(fig, destino, "06_edad_atipicos", dpi)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ct = (resenas.groupby(["calificacion", "sentimiento"]).size()
          .unstack(fill_value=0)[ORDEN_SENT])
    sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_title("Calificación vs. sentimiento (coherencia entre atributos)")
    _guardar(fig, destino, "07_calificacion_vs_sentimiento", dpi)

    fig, ax = plt.subplots(figsize=(8, 4))
    (resenas.isna().mean().mul(100).sort_values(ascending=False).head(5)
     .plot.barh(ax=ax, color="steelblue"))
    ax.set(title="Porcentaje de valores nulos por atributo (reseñas)", xlabel="% nulos")
    _guardar(fig, destino, "08_nulos_resenas", dpi)

    resumen = {
        "clientes": {"filas": len(clientes), "columnas": clientes.shape[1]},
        "resenas": {"filas": len(resenas), "columnas": resenas.shape[1]},
        "distribucion_sentimiento": resenas["sentimiento"].value_counts(normalize=True).round(4).to_dict(),
        "figuras_generadas": sorted(f.name for f in destino.glob("*.png")),
    }
    guardar_json(resumen, destino / "resumen_exploracion.json")
    print(f"[visualizacion] {len(resumen['figuras_generadas'])} figuras en {destino}")


if __name__ == "__main__":
    main()
