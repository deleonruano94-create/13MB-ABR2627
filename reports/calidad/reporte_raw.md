# Reporte de calidad de datos – etapa `raw`

Generado: 2026-11-10 15:44  
Reglas cumplidas: **19 / 19** (índice 100%)

| Regla | Dimensión ISO 25012 | Descripción | Errores | Total | Valor | Umbral | Cumple |
|---|---|---|---:|---:|---:|---:|:---:|
| completitud_edad | Completitud | Clientes sin edad informada | 243 | 10400 | 0.0234 | ≤ 0.05 | ✅ |
| completitud_tiempo_respuesta | Completitud | Reseñas sin tiempo de respuesta | 757 | 25063 | 0.0302 | ≤ 0.05 | ✅ |
| completitud_obligatorios | Completitud | Celdas vacías en campos obligatorios | 0 | 352756 | 0.0000 | ≤ 0.0 | ✅ |
| unicidad_id_cliente | Consistencia | id_cliente repetidos | 0 | 10400 | 0.0000 | ≤ 0.0 | ✅ |
| unicidad_id_resena | Consistencia | id_resena repetidos | 63 | 25063 | 0.0025 | ≤ 0.01 | ✅ |
| duplicados_resenas | Consistencia | Filas de reseñas completamente duplicadas | 63 | 25063 | 0.0025 | ≤ 0.01 | ✅ |
| rango_edad | Exactitud | Edad fuera de [18, 90] | 28 | 10400 | 0.0027 | ≤ 0.01 | ✅ |
| rango_calificacion | Exactitud | Calificación fuera de [1, 5] | 0 | 25063 | 0.0000 | ≤ 0.0 | ✅ |
| rango_antiguedad | Exactitud | Antigüedad fuera de [1, 120] meses | 0 | 10400 | 0.0000 | ≤ 0.0 | ✅ |
| rango_tiempo_respuesta | Exactitud | Tiempo de respuesta fuera de [0, 168] h | 0 | 25063 | 0.0000 | ≤ 0.01 | ✅ |
| importe_positivo | Exactitud | Importe de compra no positivo | 0 | 25063 | 0.0000 | ≤ 0.0 | ✅ |
| dominio_categoricos | Exactitud | Valores categóricos fuera del dominio del diccionario | 0 | 181578 | 0.0000 | ≤ 0.0 | ✅ |
| formato_fecha | Conformidad | Fechas que no cumplen el formato ISO YYYY-MM-DD | 0 | 25063 | 0.0000 | ≤ 0.0 | ✅ |
| actualidad_fecha | Actualidad | Fechas fuera de la ventana ['2025-01-01', '2025-12-31'] | 0 | 25063 | 0.0000 | ≤ 0.0 | ✅ |
| longitud_texto | Exactitud | Reseñas con menos de 10 caracteres | 0 | 25063 | 0.0000 | ≤ 0.0 | ✅ |
| integridad_referencial | Consistencia | Reseñas cuyo id_cliente no existe en clientes | 0 | 25063 | 0.0000 | ≤ 0.0 | ✅ |
| coherencia_calificacion_sentimiento | Consistencia | Sentimiento distinto al esperado por la calificación (1-2 Negativo, 3 Neutral, 4-5 Positivo) | 657 | 25063 | 0.0262 | ≤ 0.05 | ✅ |
| coherencia_edad_antiguedad | Consistencia | Clientes que se habrían registrado con menos de 16 años | 814 | 10157 | 0.0801 | ≤ 0.1 | ✅ |
| balance_clase_minoritaria | Adecuación al uso | Proporción de la clase minoritaria (Neutral) | 4406 | 25063 | 0.1758 | ≥ 0.1 | ✅ |
