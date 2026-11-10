# Reporte de calidad de datos – etapa `processed`

Generado: 2026-11-10 15:44  
Reglas cumplidas: **7 / 7** (índice 100%)

| Regla | Dimensión ISO 25012 | Descripción | Errores | Total | Valor | Umbral | Cumple |
|---|---|---|---:|---:|---:|---:|:---:|
| nulos | Completitud | Celdas nulas en el dataset final | 0 | 475000 | 0.0000 | ≤ 0.0 | ✅ |
| duplicados | Consistencia | Filas duplicadas en el dataset final | 0 | 25000 | 0.0000 | ≤ 0.0 | ✅ |
| rango_edad | Exactitud | Edad fuera de [18, 90] | 0 | 25000 | 0.0000 | ≤ 0.0 | ✅ |
| rango_tiempo_respuesta | Exactitud | Tiempo de respuesta fuera de rango | 0 | 25000 | 0.0000 | ≤ 0.0 | ✅ |
| dominio_categoricos | Exactitud | Categóricos fuera de dominio | 0 | 200000 | 0.0000 | ≤ 0.0 | ✅ |
| retencion_filas | Completitud | Filas finales / reseñas únicas de origen | 25000 | 25000 | 1.0000 | ≥ 0.99 | ✅ |
| distribucion_clases | Adecuación al uso | Máximo desvío de proporción de clases respecto al origen | 0 | 25000 | 0.0000 | ≤ 0.02 | ✅ |
