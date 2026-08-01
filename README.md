# Challenge 02 — Inteligencia Geo-Temporal y de Redes

**Optimización de Activos Críticos: TechLogistics S.A.**

Maestría en Ciencia de los Datos · Universidad EAFIT · Periodo 2026-1
Curso: Análisis de Datos Avanzado — Series de Tiempo · Docente: Jorge Iván Padilla-Buriticá

---

## De qué trata

TechLogistics S.A. (caso ficticio) opera dos infraestructuras georreferenciadas cuyos datos
están desconectados entre sí: una red *mesh* de sensores agroindustriales en el Oriente
Antioqueño y una red de subestaciones del sistema eléctrico nacional. Este repositorio
integra las tres capas de análisis que la junta directiva necesita —**grafos**,
**geoespacial** y **series de tiempo**— siguiendo la metodología **CRISP-DM**, para
responder una única pregunta de negocio: **dónde asignar el capital de inversión**.

### Conclusión central

> El problema de TechLogistics **no es de topología de red sino de calidad de
> instrumentación**. La red de telemetría resiste la caída de cualquiera de sus nodos con
> menos del 1 % de degradación, mientras que el ruido de los sensores destruye entre el
> 50 % y el 100 % de la información dinámica según la variable. **El capital debe
> reasignarse de redundancia de red hacia precisión de sensores y GPS diferencial.**

---

## Entregables

| Entregable | Ruta |
|---|---|
| **Cuaderno de análisis** (92 celdas, ejecutado) | [`notebooks/Challenge_02_Geo_Temporal_Redes.ipynb`](notebooks/Challenge_02_Geo_Temporal_Redes.ipynb) |
| **Informe técnico ejecutivo** (22 páginas) | [`reports/Informe_Tecnico_Challenge02.pdf`](reports/Informe_Tecnico_Challenge02.pdf) |
| **Mapas y grafo interactivos** | [`outputs/*.html`](outputs/) |

---

## Estructura del repositorio

```
.
├── data/                     Los cuatro CSV originales, sin modificar
│   ├── agro_clean.csv        agro_noise.csv
│   └── ener_clean.csv        ener_noise.csv
├── docs/                     Enunciado, checklist y diccionario del taller (PDF)
│   └── design/             Documento de diseño con supuestos y decisiones
├── notebooks/                Cuaderno de análisis — única fuente de verdad
├── figures/                  14 figuras PNG a 150 dpi generadas por el cuaderno
├── outputs/                  results.json, mapas Plotly (.html) y tablas de apoyo
├── scripts/
│   ├── run_analysis.py       Ejecuta el cuaderno de extremo a extremo
│   └── build_report.py       Construye el PDF a partir de results.json
├── reports/                  Informe técnico
└── requirements.txt
```

**Principio de diseño.** El cuaderno es la **única fuente de verdad**: escribe las figuras
y un `outputs/results.json` con cada cifra que después se cita. `build_report.py` consume
exclusivamente ese archivo y **no recalcula nada**, de modo que el informe no puede
contradecir al análisis.

---

## Reproducir

```bash
pip install -r requirements.txt
python scripts/run_analysis.py     # ejecuta el cuaderno y regenera figuras y outputs
python scripts/build_report.py     # regenera el informe PDF
```

Las semillas aleatorias están fijadas (`SEED = 42`). Probado con Python 3.12.

---

## Cobertura del taller

| Fase | Tarea | Contenido |
|---|---|---|
| **0** | Data Understanding | Verificación del pareo `clean`/`noise`, SNR medido y caracterización del *jitter* GPS |
| **1** | Tarea 1 | Geo-visualización con `scatter_mapbox` + contraste estadístico del agrupamiento espacial |
| **1** | Tarea 2 | ADF y KPSS sobre las 10 series de energía, *windowing* (ventana 50), `Ener_5`: *drift* vs random walk |
| **2** | Tarea 3 | PSD por FFT y Welch, espectrogramas `clean` vs `noise`, SNR por banda |
| **2** | Tarea 4 | Butterworth paso bajo con corte derivado del espectro, RMSE e impacto predictivo |
| **3** | Tarea 5 | Grafo `NetworkX`, centralidades, nodo cuello de botella y auditoría de robustez |
| **4** | P1 | Causalidad de Granger `Ener_10 → Ener_9` con corrección por comparaciones múltiples |
| **4** | P2 | Contraste de la premisa geo-agronómica y recomendación de inversión hídrica |
| **4** | P3 | Escalera de modelos ARIMAX: ¿mejora el AIC la centralidad del nodo? |
| **—** | V1–V4 | Las cuatro preguntas de auto-evaluación del checklist, con evidencia numérica |

---

## Hallazgos principales

1. **El SNR inyectado está entre 5.0 y 11.9 dB**, consistente con el rango declarado. El
   peor caso, `Agro_7` (5.0 dB), resulta inutilizable sin filtrar.
2. **El *jitter* GPS afecta sólo la latitud** (σ ≈ 1 133 m); la longitud no fue contaminada
   en absoluto. Además es **irreducible por suavizado**, porque cada fila es un sensor
   distinto en posición aleatoria y no una trayectoria.
3. **No existe cluster espacial de baja biomasa**: la ubicación explica η² = 0.28 % de la
   varianza del NDVI, frente al 76 % que explica el índice temporal.
4. **`Ener_5` (Costo del Gas) es un random walk con drift**, no uno puro: μ̂ = 0.0106 con
   t = 4.66, y la deriva explica exactamente todo el movimiento neto observado.
5. **El AWGN es plano** y domina por encima de f ≈ 0.01 ciclos/muestra; el SNR por banda
   cae de +27.3 dB a −111.4 dB.
6. **El Butterworth reduce el RMSE un 76 %** y el error de pronóstico a un paso un 51.6 %,
   hasta **igualar prácticamente al oráculo** entrenado sobre la señal limpia.
7. **La red es bipartita**, por lo que la *betweenness* dirigida vale exactamente 0 para
   los 70 nodos — resultado topológico, no error de cálculo.
8. **Cuello de botella: nodo 119**, pero **no hay punto único de fallo**: cero puentes,
   cero puntos de articulación y una caída máxima de eficiencia del 0.80 %.
9. **El nodo 214 del caso de negocio no es crítico**: puesto 64 de 70 en intermediación, y
   su caída incluso *mejora* la eficiencia global.
10. **La centralidad del nodo no mejora el AIC** del ARIMAX (Δ AIC = +1.50; LR p = 0.479):
    un atributo estático no puede explicar dinámica temporal.

### Sobre las premisas del encargo

Tres premisas incorporadas en las preguntas de negocio **no se sostienen al contrastarlas
con los datos**: que el nodo 214 sea un activo crítico, que exista una zona de baja
biomasa asociada a alta varianza del viento (Levene p = 0.360), y que el precio spot alto
interrumpa el flujo hacia el nodo 214 (χ² p = 0.897). Se documentan explícitamente porque
una recomendación de inversión construida sobre una premisa falsa es más costosa que la
ausencia de recomendación.

---

## Supuestos declarados

- **Los CSV no traen columna de tiempo.** Se asume muestreo regular y se construye un
  índice sintético; por eso **las frecuencias se reportan en ciclos/muestra**
  (f_s = 1), unidad invariante frente a esa elección. Como calibración *derivada*, el ciclo
  día/noche de la radiación PAR mide 125.6 muestras: si correspondiera a 24 h, el intervalo
  de muestreo sería ≈ 11.5 minutos.
- **El pareo `clean` ↔ `noise` es posicional**, y se verifica antes de usarlo: los
  identificadores de nodo coinciden fila a fila en los 2 000 registros.
- **Cada fila es una observación de un enlace** `Source_Node → Target_Node` (datos panel),
  no una serie univariada pura.
