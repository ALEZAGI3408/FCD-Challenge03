# Diseño — Challenge 03: Inteligencia Geo-Temporal y de Redes

**Fecha:** 2026-08-01
**Curso:** Fundamentos en Ciencia de Datos — Maestría en Ciencia de los Datos, EAFIT
**Autores:** Samuel Alarcón · Juan Alberto Rodríguez · Alejandro Zapata Giraldo
**Caso:** TechLogistics S.A. (ficticio)

## 1. Objetivo

Entregar los tres activos exigidos por el checklist de evaluación:

1. Repositorio Git con historial de commits progresivo y `README.md` descriptivo.
2. Jupyter Notebook documentado (cada bloque de código precedido de Markdown que explica la lógica técnica).
3. Informe técnico en PDF que responda las preguntas de negocio con evidencia gráfica.

## 2. Estructura del repositorio

```
Lecture_03_Challenge/
├── README.md                 Descripción, cómo reproducir, resumen de hallazgos
├── requirements.txt          Dependencias fijadas
├── .gitignore
├── data/                     agro_{clean,noise}.csv, ener_{clean,noise}.csv
├── docs/                     PDFs originales del taller + este spec
├── notebooks/
│   └── Challenge_03_Geo_Temporal_Redes.ipynb   ← fuente única de verdad
├── figures/                  PNG generados por el notebook
├── outputs/                  mapas Plotly (.html), results.json, tablas .csv
├── scripts/
│   ├── run_analysis.py       ejecuta el notebook headless (nbconvert)
│   └── build_report.py       arma el PDF con ReportLab desde results.json + figures/
└── reports/
    └── Informe_Tecnico_Challenge03.pdf
```

**Principio de diseño:** el notebook es la única fuente de verdad. Escribe todas las
figuras y un `outputs/results.json` con cada cifra citada. `build_report.py` sólo
consume ese JSON. El informe no puede contradecir al análisis porque no recalcula nada.

## 3. Supuestos explícitos

- **Sin columna temporal.** Los CSV no traen timestamp. Se asume muestreo regular y se
  construye un `DatetimeIndex` horario sintético (`2025-01-01 00:00`, 2000 registros).
  Las frecuencias de FFT se reportan en **ciclos/muestra** (f_s = 1), que es la unidad
  invariante frente a esa elección; el periodo en horas se deriva de ella.
- **Pareo clean↔noise por índice de fila.** Verificado: `Source_Node` y `Target_Node`
  son idénticos fila a fila entre `clean` y `noise` en ambos datasets, lo que confirma
  que la contaminación es aditiva sobre las mismas observaciones.
- **Datos panel, no serie única.** Cada fila es una observación de un enlace
  (Source_Node → Target_Node). Para el análisis temporal se trata la columna como una
  serie ordenada por índice, que es lo que el enunciado pide.

## 4. Hallazgos verificados que condicionan el diseño

Comprobados sobre los datos antes de escribir el análisis:

1. **El grafo es bipartito.** Agro: fuentes 1–14, destinos 15–29. Energía: fuentes
   100–119, destinos 200–249. No existe ningún nodo que sea a la vez origen y destino.
   Consecuencia: en el `DiGraph`, **toda ruta dirigida tiene longitud 1**, por lo que la
   betweenness dirigida es exactamente 0 para los 70 nodos de energía y los 29 de agro.
   Esto no es un fallo del cálculo sino un resultado topológico y se reporta como tal.
   El "nodo cuello de botella" se identifica con tres métricas complementarias:
   - betweenness sobre la vista no dirigida (los gateways sí son puentes entre sensores),
   - grado ponderado por volumen real de telemetría (nº de registros por enlace),
   - centralidad de carga y análisis de fallo simulado.
2. **El jitter GPS sólo afecta `Latitude`.** `Longitude` es idéntica entre `clean` y
   `noise` en ambos datasets (desviación del error = 0). Se reporta explícitamente,
   porque cambia la estrategia de filtrado espacial.
3. **SNR medido** (10·log10(var_señal / var_ruido), ruido = noise − clean):
   agro 5.0–11.6 dB, energía 6.2–11.9 dB. Consistente con el rango [5, 12] dB del
   enunciado. Peores casos: `Agro_7` (5.0 dB) y `Ener_10` (6.15 dB).
4. **Multiplicidad de enlaces.** En energía hay 865 pares únicos con hasta 9
   repeticiones; el peso del enlace = nº de observaciones es una medida directa de
   volumen de telemetría.

## 5. Contenido analítico

| Fase | Tarea | Método |
|---|---|---|
| 1 | T1 Geo-visualización | `plotly.express.scatter_map`, color=NDVI (Agro_5), size=Humedad (Agro_1); + KMeans para detectar clusters de biomasa baja; mapa de calor |
| 1 | T2 Estacionariedad | ADF sobre las 10 series de energía; rolling mean/var (ventana 50); Ener_5 drift vs random walk vía ADF con constante+tendencia y test sobre la media de las primeras diferencias |
| 2 | T3 FFT / espectrograma | PSD por FFT y Welch de Ener_4; espectrograma `scipy.signal.spectrogram` clean vs noise; diferencia de PSD para localizar la banda del ruido |
| 2 | T4 Filtrado | Butterworth paso bajo sobre `Agro_3_noise`, corte elegido desde el espectro; RMSE noise-vs-clean y filtrada-vs-clean; barrido de frecuencia de corte; impacto predictivo vía AR |
| 3 | T5 Grafos | `NetworkX` DiGraph; grado, in/out, betweenness (dirigida y no dirigida), carga; identificación del cuello de botella; visualización |
| 4 | P1 | Granger Ener_10 → Ener_9 (sobre series estacionarias) + simulación de fallo del nodo de mayor betweenness |
| 4 | P2 | Suavizado espacial del jitter, NDVI mínimo vs varianza del viento (Agro_10), recomendación de inversión hídrica |
| 4 | P3 | ARIMAX de Ener_1 con exógenas Temperatura (Ener_3) y centralidad del Source_Node; comparación de AIC con y sin la centralidad |

Además, las 4 preguntas de auto-evaluación del checklist (correlación espuria,
impacto del ruido de 5 dB sobre coeficientes ARMA, nodos "bridge", geografía y varianza)
se responden en el informe con evidencia numérica generada en el notebook.

## 6. Reproducibilidad

`pip install -r requirements.txt`, luego `python scripts/run_analysis.py` (ejecuta el
notebook y regenera figuras/outputs) y `python scripts/build_report.py` (regenera el PDF).
Semillas fijadas donde hay aleatoriedad (KMeans, layouts de grafo).
