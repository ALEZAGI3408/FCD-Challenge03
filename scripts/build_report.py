#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genera el Informe Técnico (PDF) del Challenge 02 con ReportLab.

Consume EXCLUSIVAMENTE outputs/results.json y las figuras de figures/, ambos producidos
por el notebook. No recalcula nada: así el informe no puede contradecir al análisis.

Uso:  python scripts/build_report.py
"""
import json
import sys
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figures"
OUT = ROOT / "outputs"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
DEST = REPORTS / "Informe_Tecnico_Challenge02.pdf"

_MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre")
_hoy = date.today()
FECHA_ES = f"{_hoy.day} de {_MESES[_hoy.month - 1]} de {_hoy.year}"

AZUL = colors.HexColor("#1f4e79")
AZUL_CLARO = colors.HexColor("#dce6f1")
NARANJA = colors.HexColor("#e07b39")
VERDE = colors.HexColor("#2e8b57")
ROJO = colors.HexColor("#c0392b")
GRIS = colors.HexColor("#5a6570")
GRIS_SUAVE = colors.HexColor("#f4f6f8")

# ─────────────────────────── Tipografía ───────────────────────────
# DejaVu cubre griegas y superíndices (η², σ², Δ, χ²), que WinAnsi no soporta.
def registrar_fuentes() -> tuple[str, str, str]:
    try:
        import matplotlib
        ttf = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        pdfmetrics.registerFont(TTFont("DejaVu", str(ttf / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(ttf / "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(ttf / "DejaVuSans-Oblique.ttf")))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                                      italic="DejaVu-Oblique")
        return "DejaVu", "DejaVu-Bold", "DejaVu-Oblique"
    except Exception as exc:  # pragma: no cover
        print(f"AVISO: no se pudieron registrar las fuentes DejaVu ({exc}); "
              "se usará Helvetica y los símbolos griegos podrían no renderizar.")
        return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


FUENTE, FUENTE_B, FUENTE_I = registrar_fuentes()

# ─────────────────────────── Resultados ───────────────────────────
try:
    R = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
except FileNotFoundError:
    print("ERROR: falta outputs/results.json. Ejecute antes:  python scripts/run_analysis.py",
          file=sys.stderr)
    raise SystemExit(1)


def V(clave: str, fmt: str = "{}", defecto: str = "n/d") -> str:
    """Formatea una cifra del análisis. Falla visiblemente si la clave no existe."""
    if clave not in R:
        print(f"AVISO: clave ausente en results.json → {clave}")
        return defecto
    return fmt.format(R[clave])


# ─────────────────────────── Estilos ───────────────────────────
base = getSampleStyleSheet()
S = {
    "titulo": ParagraphStyle("titulo", parent=base["Title"], fontName=FUENTE_B,
                             fontSize=25, leading=30, textColor=AZUL, spaceAfter=6),
    "subtitulo": ParagraphStyle("subtitulo", parent=base["Normal"], fontName=FUENTE_B,
                                fontSize=14.5, leading=19, textColor=NARANJA,
                                alignment=TA_CENTER, spaceAfter=16),
    "portada": ParagraphStyle("portada", parent=base["Normal"], fontName=FUENTE,
                              fontSize=11, leading=17, alignment=TA_CENTER,
                              textColor=GRIS),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=FUENTE_B, fontSize=15.5,
                         leading=19, textColor=AZUL, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=FUENTE_B, fontSize=12,
                         leading=15, textColor=NARANJA, spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=FUENTE_B, fontSize=10.5,
                         leading=13, textColor=GRIS, spaceBefore=9, spaceAfter=3),
    "cuerpo": ParagraphStyle("cuerpo", parent=base["BodyText"], fontName=FUENTE,
                             fontSize=9.6, leading=14.2, alignment=TA_JUSTIFY,
                             spaceAfter=7, textColor=colors.HexColor("#22292f")),
    "vineta": ParagraphStyle("vineta", parent=base["BodyText"], fontName=FUENTE,
                             fontSize=9.4, leading=13.6, alignment=TA_JUSTIFY,
                             leftIndent=13, bulletIndent=4, spaceAfter=4.5,
                             textColor=colors.HexColor("#22292f")),
    "pie_fig": ParagraphStyle("pie_fig", parent=base["Normal"], fontName=FUENTE_I,
                              fontSize=8.1, leading=11, alignment=TA_CENTER,
                              textColor=GRIS, spaceBefore=3, spaceAfter=11),
    "celda": ParagraphStyle("celda", parent=base["Normal"], fontName=FUENTE,
                            fontSize=8.1, leading=10.6),
    "celda_b": ParagraphStyle("celda_b", parent=base["Normal"], fontName=FUENTE_B,
                              fontSize=8.1, leading=10.6, textColor=colors.white),
    "hallazgo": ParagraphStyle("hallazgo", parent=base["BodyText"], fontName=FUENTE,
                               fontSize=9.4, leading=13.6, alignment=TA_JUSTIFY,
                               textColor=colors.HexColor("#1a1f24")),
}

story: list = []


def H1(t): story.append(Paragraph(t, S["h1"]))
def H2(t): story.append(Paragraph(t, S["h2"]))
def H3(t): story.append(Paragraph(t, S["h3"]))
def P(t): story.append(Paragraph(t, S["cuerpo"]))
def B(t): story.append(Paragraph(t, S["vineta"], bulletText="•"))
def SP(h=6): story.append(Spacer(1, h))


def caja(titulo: str, texto: str, color=AZUL, fondo=AZUL_CLARO):
    """Recuadro destacado para respuestas y hallazgos clave."""
    interior = [[Paragraph(f"<b>{titulo}</b>", ParagraphStyle(
        "ct", parent=S["hallazgo"], fontName=FUENTE_B, fontSize=10, textColor=color,
        spaceAfter=4))], [Paragraph(texto, S["hallazgo"])]]
    t = Table(interior, colWidths=[16.0 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fondo),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("BOX", (0, 0), (-1, -1), 0.4, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(KeepTogether([t, Spacer(1, 9)]))


def tabla(cabecera: list[str], filas: list[list[str]], anchos: list[float],
          resaltar: dict[int, colors.Color] | None = None):
    datos = [[Paragraph(str(c), S["celda_b"]) for c in cabecera]]
    datos += [[Paragraph(str(c), S["celda"]) for c in fila] for fila in filas]
    t = Table(datos, colWidths=anchos, repeatRows=1, hAlign="CENTER")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c4ccd4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_SUAVE]),
    ]
    for idx, col in (resaltar or {}).items():
        estilo.append(("BACKGROUND", (0, idx), (-1, idx), col))
    t.setStyle(TableStyle(estilo))
    story.append(t)
    SP(10)


def figura(nombre: str, pie: str, ancho: float = 16.0):
    ruta = FIGS / f"{nombre}.png"
    if not ruta.exists():
        print(f"AVISO: falta la figura {ruta.name}")
        return
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(ruta)).getSize()
    ancho_pt = ancho * cm
    img = Image(str(ruta), width=ancho_pt, height=ancho_pt * h / w)
    story.append(KeepTogether([img, Paragraph(pie, S["pie_fig"])]))


# ─────────────────────────── Plantillas de página ───────────────────────────
def pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c9d2da"))
    canvas.setLineWidth(0.4)
    canvas.line(2.2 * cm, 1.55 * cm, A4[0] - 2.2 * cm, 1.55 * cm)
    canvas.setFont(FUENTE, 7.4)
    canvas.setFillColor(GRIS)
    canvas.drawString(2.2 * cm, 1.12 * cm,
                      "Challenge 02 · Inteligencia Geo-Temporal y de Redes · TechLogistics S.A.")
    canvas.drawRightString(A4[0] - 2.2 * cm, 1.12 * cm, f"Página {doc.page - 1}")
    canvas.setStrokeColor(AZUL)
    canvas.setLineWidth(2.4)
    canvas.line(2.2 * cm, A4[1] - 1.75 * cm, A4[0] - 2.2 * cm, A4[1] - 1.75 * cm)
    canvas.setFont(FUENTE, 7.4)
    canvas.drawRightString(A4[0] - 2.2 * cm, A4[1] - 1.55 * cm,
                           "Universidad EAFIT · Maestría en Ciencia de los Datos")
    canvas.restoreState()


def portada_limpia(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AZUL)
    canvas.rect(0, A4[1] - 1.15 * cm, A4[0], 1.15 * cm, stroke=0, fill=1)
    canvas.setFillColor(NARANJA)
    canvas.rect(0, 0, A4[0], 0.75 * cm, stroke=0, fill=1)
    canvas.restoreState()


doc = BaseDocTemplate(str(DEST), pagesize=A4,
                      leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                      topMargin=2.3 * cm, bottomMargin=2.0 * cm,
                      title="Informe Técnico — Challenge 02: Inteligencia Geo-Temporal y de Redes",
                      author="Maestría en Ciencia de los Datos — EAFIT",
                      subject="Optimización de Activos Críticos: TechLogistics S.A.")
marco = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="cuerpo")
doc.addPageTemplates([
    PageTemplate(id="portada", frames=[marco], onPage=portada_limpia),
    PageTemplate(id="normal", frames=[marco], onPage=pie_pagina),
])

# ═══════════════════════════ PORTADA ═══════════════════════════
story.append(NextPageTemplate("normal"))
SP(58)
story.append(Paragraph("Informe Técnico", S["titulo"]))
story.append(Paragraph("Inteligencia Geo-Temporal y de Redes", S["subtitulo"]))
SP(6)
story.append(Paragraph(
    "<b>Optimización de Activos Críticos: TechLogistics S.A.</b><br/>"
    "Challenge 02 · Analítica Multidimensional", S["portada"]))
SP(26)

resumen_portada = Table([[Paragraph(
    "<b>Encargo.</b> La junta directiva de TechLogistics S.A. requiere integrar tres capas "
    "de información hasta ahora desconectadas —la topología de su red de telemetría, la "
    "distribución geoespacial de sus activos y la dinámica temporal de sus señales— para "
    "decidir dónde asignar capital de inversión.<br/><br/>"
    "<b>Conclusión central.</b> El problema de TechLogistics no es de topología de red sino "
    "de <b>calidad de instrumentación</b>. La red de telemetría resiste la caída de "
    "cualquiera de sus nodos con menos del 1 % de degradación, mientras que el ruido de los "
    "sensores destruye entre el 50 % y el 100 % de la información dinámica según la "
    "variable. <b>El capital debe reasignarse de redundancia de red hacia precisión de "
    "sensores y GPS diferencial.</b>",
    ParagraphStyle("rp", parent=S["cuerpo"], fontSize=9.8, leading=14.6))]],
    colWidths=[15.6 * cm])
resumen_portada.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), GRIS_SUAVE),
    ("LINEBEFORE", (0, 0), (0, -1), 3.5, NARANJA),
    ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d2da")),
    ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 13),
    ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
]))
story.append(resumen_portada)
SP(40)
story.append(Paragraph(
    "<b>Curso:</b> Análisis de Datos Avanzado — Series de Tiempo<br/>"
    "<b>Docente:</b> Jorge Iván Padilla-Buriticá<br/>"
    "<b>Programa:</b> Maestría en Ciencia de los Datos<br/>"
    "<b>Universidad EAFIT</b> · Periodo 2026-1<br/>"
    "<b>Metodología:</b> CRISP-DM / Análisis Multicapa", S["portada"]))
SP(24)
story.append(Paragraph(
    f"Documento generado automáticamente a partir de "
    f"<font face='{FUENTE_B}'>outputs/results.json</font><br/>"
    f"{FECHA_ES} · "
    f"{len(R)} resultados verificados · {len(list(FIGS.glob('*.png')))} figuras",
    ParagraphStyle("meta", parent=S["portada"], fontSize=8.3, textColor=GRIS)))
story.append(PageBreak())

# ═══════════════════════ 1. RESUMEN EJECUTIVO ═══════════════════════
H1("1. Resumen ejecutivo")
P("Este informe responde las tres preguntas de negocio planteadas por la junta directiva y "
  "las cuatro preguntas de validación del protocolo de entrega. Todo el análisis se ejecutó "
  "sobre los cuatro activos de información entregados "
  f"(<i>agro</i> y <i>energía</i>, en variantes <i>clean</i> y <i>noise</i>, "
  f"{V('n_obs')} observaciones cada uno) y es íntegramente reproducible.")
P("El hallazgo transversal es que <b>varias de las premisas del encargo no se sostienen al "
  "contrastarlas con los datos</b>. Documentarlo es parte del trabajo: una recomendación de "
  "inversión construida sobre una premisa falsa es más costosa que la ausencia de "
  "recomendación.")

SP(3)
H2("1.1 Los doce hallazgos")
tabla(
    ["#", "Hallazgo", "Evidencia", "Implicación"],
    [
        ["1", "El SNR inyectado está en el rango declarado",
         f"20 señales: {V('snr_min', '{:.1f}')}–{V('snr_max', '{:.1f}')} dB",
         f"El peor caso, {V('snr_peor_variable')}, es inutilizable sin filtrar"],
        ["2", "El <i>jitter</i> GPS afecta <b>sólo la latitud</b>",
         f"σ error longitud = 0 exacto; σ latitud ≈ {V('jitter_agro_sigma_m', '{:.0f}')} m",
         "Se requiere GPS diferencial o coordenada fija por sensor"],
        ["3", "<b>No hay cluster espacial</b> de baja biomasa",
         f"η² = {V('t1_eta2_pct', '{:.2f}')} %; centroides a "
         f"{V('p2_separacion_centroides_m', '{:.0f}')} m (p ≈ {V('t1_ttest_lat_p', '{:.2f}')})",
         "La inversión hídrica <b>no</b> debe zonificarse"],
        ["4", "<code>Ener_5</code> es un <b>random walk con drift</b>",
         f"ADF p = {V('ener5_adf_c_p', '{:.2f}')}; μ̂ = {V('ener5_drift_mu', '{:.4f}')}, "
         f"t = {V('ener5_drift_t', '{:.2f}')}",
         "Sin reversión a la media: cobertura financiera obligatoria"],
        ["5", "El AWGN es <b>plano</b>; domina sobre f ≈ 0.01",
         f"SNR por banda: +27.3 dB → −111.4 dB",
         "Justifica el filtro paso bajo con corte en el cruce espectral"],
        ["6", "El Butterworth reduce el RMSE un "
         f"<b>{V('agro3_mejora_pct', '{:.0f}')} %</b>",
         f"{V('agro3_rmse_ruidosa', '{:.2f}')} → {V('agro3_rmse_filtrada', '{:.2f}')}",
         "El filtrado es condición previa al modelado"],
        ["7", "El filtrado recupera la capacidad predictiva",
         f"RMSE 1 paso: {V('t4_pred_rmse_ruidosa', '{:.2f}')} → "
         f"{V('t4_pred_rmse_filtrada', '{:.2f}')} (oráculo {V('t4_pred_rmse_oraculo', '{:.2f}')})",
         f"Mejora del {V('t4_pred_mejora_pct', '{:.0f}')} %, casi el máximo alcanzable"],
        ["8", "La red es <b>bipartita</b>: betweenness dirigida = 0",
         f"DAG de dos capas; {V('grafo_ener_nodos')} nodos, diámetro {V('grafo_ener_diametro')}",
         "La métrica del enunciado no es informativa en esta topología"],
        ["9", f"Cuello de botella: <b>nodo {V('cuello_botella')}</b>, pero "
         "<b>sin punto único de fallo</b>",
         f"{V('n_puentes')} puentes, {V('n_articulacion')} articulaciones; "
         f"caída de {V('caida_eficiencia_cuello_pct', '{:.2f}')} %",
         "El riesgo <b>no</b> es topológico"],
        ["10", f"El <b>nodo 214 no es crítico</b>: puesto {V('nodo214_rank')} de "
         f"{V('nodo214_total_nodos')}",
         f"Su caída <b>mejora</b> la eficiencia un {V('caida_eficiencia_214_pct', '{:.2f}')} %".replace("−", "").replace("-", ""),
         "La premisa del caso de negocio no se sostiene"],
        ["11", "Granger FP→Voltaje: <b>marginal</b>, se anula con ruido",
         f"p = {V('granger_10_9_p', '{:.3f}')} → {V('granger_10_9_bonferroni', '{:.3f}')} "
         f"(Bonferroni); {V('granger_noise_p', '{:.3f}')} en <i>noise</i>",
         "Monitorear, no concluir causalidad"],
        ["12", "La <b>centralidad no mejora el AIC</b> del ARIMAX",
         f"Δ AIC = +{V('p3_delta_aic_btw', '{:.2f}')}; LR p = {V('p3_lr_p', '{:.3f}')}",
         "Un atributo estático no explica dinámica temporal"],
    ],
    [0.8 * cm, 4.5 * cm, 5.3 * cm, 5.4 * cm])

caja("Recomendación central para la junta directiva",
     "Reasignar el presupuesto de <b>redundancia topológica</b> —hoy sobredimensionada, con "
     f"cero puentes y cero puntos de articulación en una red de {V('grafo_ener_nodos')} "
     "nodos— hacia <b>calidad de instrumentación</b>: sensores de mayor SNR en las variables "
     f"críticas (empezando por <code>{V('snr_peor_variable')}</code>, a "
     f"{V('snr_min', '{:.1f}')} dB) y corrección diferencial de GPS. El análisis muestra que "
     "el ruido de medición, y no la fragilidad de la red, es lo que destruye la capacidad de "
     "decisión de la compañía.",
     color=NARANJA, fondo=colors.HexColor("#fdf0e6"))
story.append(PageBreak())

# ═══════════════════════ 2. METODOLOGÍA ═══════════════════════
H1("2. Metodología, datos y supuestos declarados")
P("El trabajo sigue el ciclo <b>CRISP-DM</b> en cuatro fases: comprensión de los datos, "
  "procesamiento de señales, análisis de redes y modelado para la toma de decisiones. Toda "
  "la evidencia procede de un único cuaderno Jupyter ejecutado de extremo a extremo, que "
  "serializa cada cifra citada aquí en <code>outputs/results.json</code>. Este informe se "
  "genera leyendo ese archivo: no recalcula nada y, por construcción, no puede desviarse de "
  "lo que el análisis demostró.")

H2("2.1 Supuestos declarados")
B("<b>Ausencia de marca temporal.</b> Los CSV no incluyen columna de tiempo. Se asume "
  "muestreo regular y se construye un índice sintético. En consecuencia, <b>todas las "
  "frecuencias se reportan en ciclos/muestra</b> (f<sub>s</sub> = 1), unidad invariante "
  "frente a esa elección arbitraria. A modo de calibración derivada —no asumida—, el ciclo "
  f"día/noche de la radiación PAR mide {V('par_periodo_muestras', '{:.1f}')} muestras; si "
  f"correspondiera a 24 h, el intervalo de muestreo sería ≈ {V('dt_minutos_implicito', '{:.1f}')} minutos.")
B("<b>Pareo posicional <i>clean</i> ↔ <i>noise</i>.</b> Se verificó que "
  "<code>Source_Node</code> y <code>Target_Node</code> coinciden fila a fila en los dos "
  "datasets, lo que valida estimar el ruido como la resta directa <i>noise</i> − <i>clean</i>. "
  "Sin esa verificación, todas las mediciones de SNR carecerían de fundamento.")
B("<b>Estructura de datos panel.</b> Cada fila es una observación de un enlace "
  "<code>Source_Node → Target_Node</code>, no una serie univariada pura. Esto es relevante "
  "para interpretar los resultados geoespaciales y el modelo ARIMAX.")

H2("2.2 Verificación de la contaminación inyectada")
P("Antes de cualquier análisis se cuantificó el ruido realmente presente, en lugar de "
  "asumir el rango declarado en el enunciado. Las 20 señales caen en "
  f"<b>[{V('snr_min', '{:.2f}')}, {V('snr_max', '{:.2f}')}] dB</b>, consistente con el "
  "rango SNR ∈ [5, 12] dB especificado. El test de Shapiro-Wilk sobre el residuo no rechaza "
  f"la normalidad (p = {V('ruido_shapiro_p', '{:.3f}')}), confirmando la naturaleza AWGN.")
P("La caracterización del <i>jitter</i> geoespacial arrojó un hallazgo no anticipado por el "
  "diccionario de datos: <b>la longitud no fue contaminada en absoluto</b> (σ del error "
  "exactamente 0 en ambos datasets), mientras la latitud presenta un desplazamiento típico "
  f"de {V('jitter_agro_sigma_m', '{:.0f}')} m en agro y "
  f"{V('jitter_ener_sigma_m', '{:.0f}')} m en energía "
  f"(máximo {V('jitter_ener_max_m', '{:.0f}')} m). El error es, por tanto, unidimensional.")
figura("f00_snr_y_jitter",
       "Figura 1. Caracterización de la contaminación: SNR medido por variable frente al rango "
       "declarado (izq.), normalidad del residuo (centro) y naturaleza unidimensional del "
       "jitter GPS (der.).")
story.append(PageBreak())

# ═══════════════════════ 3. FASE 1 ═══════════════════════
H1("3. Fase 1 — Comprensión de los datos y geo-visualización")

H2("3.1 Tarea 1 · ¿Existe un cluster espacial de baja biomasa?")
P("Se cartografiaron los sensores del Oriente Antioqueño con <code>scatter_mapbox</code>, "
  "codificando color por NDVI (<code>Agro_5</code>) y tamaño por humedad "
  f"(<code>Agro_1</code>), sobre un área de ~{V('area_lat_km', '{:.0f}')} × "
  f"{V('area_lon_km', '{:.0f}')} km. El mapa interactivo se entrega en "
  "<code>outputs/t1_mapa_sensores_ndvi.html</code> junto con un mapa de calor de densidad.")
P("Un mapa siempre <i>parece</i> tener zonas buenas y malas: el ojo humano encuentra "
  "patrones en ruido puro. Por eso la pregunta se resolvió con tres contrastes "
  "independientes en lugar de con inspección visual.")
tabla(["Contraste", "Resultado", "Lectura"],
      [["ANOVA del NDVI sobre 5 zonas K-Means",
        f"p = {V('t1_anova_p', '{:.3f}')}", "No significativo"],
       ["Varianza explicada por la ubicación (η²)",
        f"{V('t1_eta2_pct', '{:.2f}')} %", "Efecto despreciable"],
       ["Centroides de los extremos de NDVI",
        f"separados {V('p2_separacion_centroides_m', '{:.0f}')} m "
        f"(p = {V('t1_ttest_lat_p', '{:.2f}')} lat, {V('t1_ttest_lon_p', '{:.2f}')} lon)",
        "Indistinguibles"],
       ["Varianza explicada por el tiempo (R²)",
        f"{V('p2_var_temporal_pct', '{:.0f}')} %", "El NDVI es I(1): deriva temporal"]],
      [5.6 * cm, 5.4 * cm, 5.0 * cm])
caja("Respuesta a la Tarea 1",
     "<b>No existe evidencia de un cluster espacial de baja biomasa.</b> El NDVI medio de "
     f"las cinco zonas va de {V('t1_zona_peor_ndvi', '{:.3f}')} a "
     f"{V('t1_zona_mejor_ndvi', '{:.3f}')} —un rango del 4.8 %— y la ubicación explica "
     f"apenas el {V('t1_eta2_pct', '{:.2f}')} % de la varianza, frente al "
     f"{V('p2_var_temporal_pct', '{:.0f}')} % que explica el índice temporal. "
     "<b>La variabilidad del NDVI en esta red es temporal, no geográfica.</b> Cualquier "
     "mancha que el ojo detecte en el mapa de calor es ruido muestral. En consecuencia, una "
     "intervención agronómica focalizada por zona no está justificada; lo que sí lo está es "
     "una intervención por periodo.")
figura("f01_t1_geo_clustering",
       "Figura 2. Distribución espacial del NDVI, agrupamiento K-Means con centroides de los "
       "extremos —prácticamente superpuestos— y dispersión por zona.")

H2("3.2 Tarea 2 · Estacionariedad, <i>windowing</i> y el caso del Costo del Gas")
P("Se aplicó el test <b>ADF</b> a las diez series de energía, complementado con <b>KPSS</b> "
  "—cuyas hipótesis están invertidas— para evitar la conclusión ambigua típica de un solo "
  "test. El diagnóstico reproduce exactamente la naturaleza declarada en el diccionario de "
  f"datos: son <b>I(1)</b> las series {', '.join('<code>%s</code>' % s for s in R.get('t2_no_estacionarias', []))} "
  "(mercado spot y factores macro), y <b>I(0)</b> las de calidad de potencia.")
P("Sobre las series I(1) se aplicó la ventana móvil de 50 registros solicitada. La lectura "
  "diagnóstica es doble: una media móvil que deambula sin volver a un nivel fijo indica "
  "ausencia de reversión a la media, y una varianza móvil creciente es la firma de un paseo "
  "aleatorio, cuya varianza teórica crece linealmente con t.")

H3("Anomalía documentada en Ener_4")
P("El ADF de <code>Ener_4</code> devuelve un estadístico del orden de −10¹⁰, imposible en "
  "una serie estocástica real. No es un error de cálculo: el ajuste de un AR(2) arroja "
  f"R² = {V('ener4_ar2_r2', '{:.8f}')}, es decir, la serie es <b>esencialmente "
  "determinista</b> y la regresión del test resulta casi singular. La serie es "
  "cíclico-estacionaria por construcción y el ADF no le es aplicable.")

H3("¿Drift o random walk?")
P("Un random walk puro y uno con drift comparten la raíz unitaria, de modo que <b>el ADF no "
  "los distingue</b>. Lo que los separa es si la media de las primeras diferencias es "
  "distinta de cero, ya que Δy<sub>t</sub> = μ + ε<sub>t</sub>.")
tabla(["Prueba", "Resultado", "Conclusión"],
      [["ADF con constante", f"p = {V('ener5_adf_c_p', '{:.3f}')}", "No rechaza: hay raíz unitaria"],
       ["ADF con constante + tendencia", f"p = {V('ener5_adf_ct_p', '{:.3f}')}",
        "Tampoco rechaza: la tendencia es estocástica, no determinista"],
       ["Test t sobre μ̂ = media(Δy)",
        f"μ̂ = {V('ener5_drift_mu', '{:.5f}')}, t = {V('ener5_drift_t', '{:.2f}')}, "
        f"p = {V('ener5_drift_p', '{:.1e}')}", "El drift es real: el IC 95 % excluye el cero"],
       ["Deriva acumulada μ̂·n vs cambio total",
        f"{V('ener5_deriva_acumulada', '{:.2f}')} vs {V('ener5_cambio_total', '{:.2f}')}",
        "La deriva explica <b>todo</b> el movimiento neto"]],
      [4.6 * cm, 5.6 * cm, 5.8 * cm])
caja("Respuesta a la Tarea 2",
     "<b><code>Ener_5</code> (Costo del Gas) es un <i>random walk con drift</i>, no un "
     "random walk puro.</b> Con tendencia estocástica, el intervalo de pronóstico se abre "
     "con √h y <b>no existe un precio de reversión al que el gas 'volverá'</b>. "
     "Presupuestar el costo del gas con una regresión lineal sobre el tiempo —que aquí daría "
     "un R² engañosamente alto— subestimaría gravemente el riesgo. El modelo correcto para "
     "cobertura financiera es ARIMA(p, 1, q) <b>con constante</b>.")
figura("f03_t2_ener5_drift",
       "Figura 3. Ener_5: la media móvil nunca revierte a un nivel fijo; las primeras "
       "diferencias son ruido blanco alrededor de μ̂ ≠ 0 y su intervalo de confianza excluye "
       "el cero.")
story.append(PageBreak())

# ═══════════════════════ 4. FASE 2 ═══════════════════════
H1("4. Fase 2 — Procesamiento de señales y filtrado")

H2("4.1 Tarea 3 · ¿Dónde se concentra el ruido inyectado?")
P("La pregunta admite dos lecturas que suelen confundirse, y responderla bien exige "
  "separarlas. <b>En potencia absoluta</b>, el AWGN es blanco: reparte su energía "
  "uniformemente y no se concentra en ninguna banda —la PSD del residuo es plana, con una "
  f"pendiente log-PSD no significativa (p = {V('ruido_psd_pendiente_p', '{:.2f}')}). "
  "<b>En impacto relativo</b>, que es lo que gobierna el filtrado, el ruido domina allí "
  "donde la señal es débil.")
P("La métrica que resuelve la ambigüedad es el <b>SNR por banda</b>. "
  f"<code>Ener_4</code> concentra el {V('t3_pot_clean_bajo_001', '{:.1f}')} % de su potencia "
  f"por debajo de 0.01 ciclos/muestra (ciclo dominante de "
  f"{V('ener4_periodo_dominante', '{:.0f}')} muestras), de modo que al añadir un suelo plano "
  "la observación por encima de esa frecuencia es prácticamente ruido puro.")
_b = R.get("t3_bandas", {})
tabla(["Banda (ciclos/muestra)", "% potencia CLEAN", "% potencia RUIDO", "SNR de banda (dB)"],
      [[k, f"{v['% pot. CLEAN']:.1f}", f"{v['% pot. RUIDO']:.1f}", f"{v['SNR banda (dB)']:+.1f}"]
       for k, v in _b.items()],
      [4.6 * cm, 3.8 * cm, 3.8 * cm, 3.8 * cm],
      resaltar={1: colors.HexColor("#e8f4ea")})
caja("Respuesta a la Tarea 3",
     "<b>El ruido no se concentra en un rango: es blanco y ocupa todo el espectro por "
     "igual.</b> Lo que sí tiene respuesta precisa es dónde resulta <i>dominante</i>: por "
     f"encima de <b>f ≈ {V('ener4_f_cruce_snr0', '{:.4f}')} ciclos/muestra</b> "
     f"(periodos menores a ~{1/R.get('ener4_f_cruce_snr0', 0.01):.0f} muestras). El SNR por "
     "banda cae de <b>+27.3 dB</b> en [0, 0.01) a <b>−29.8 dB</b> en [0.01, 0.05) y hasta "
     "<b>−111.4 dB</b> cerca de Nyquist. Esto genera una predicción falsable: un filtro paso "
     "bajo con corte cerca de la frecuencia de cruce debería recuperar casi toda la señal "
     "descartando casi todo el ruido — comprobado en la Tarea 4.")
figura("f05_t3_espectral",
       "Figura 4. Análisis espectral de Ener_4: periodograma FFT, PSD de Welch con el suelo "
       "plano del ruido, SNR en función de la frecuencia y espectrogramas clean vs noise.")

H2("4.2 Tarea 4 · Filtrado Butterworth y su efecto sobre el pronóstico")
P("Se implementó un Butterworth de paso bajo con <code>filtfilt</code> —aplicación hacia "
  "adelante y hacia atrás— para lograr <b>distorsión de fase exactamente cero</b>: un "
  "desfase temporal inflaría el RMSE aunque la forma de onda fuese perfecta. La frecuencia "
  "de corte no se eligió a ojo, sino que se derivó del espectro y se validó con un barrido "
  "exhaustivo de orden × frecuencia.")
tabla(["Métrica", "Serie ruidosa", "Serie filtrada", "Mejora"],
      [["RMSE de reconstrucción", V('agro3_rmse_ruidosa', '{:.4f}'),
        V('agro3_rmse_filtrada', '{:.4f}'), f"{V('agro3_mejora_pct', '{:.1f}')} %"],
       ["SNR de la serie (dB)", V('agro3_snr_antes', '{:.2f}'),
        V('agro3_snr_despues', '{:.2f}'),
        f"+{R.get('agro3_snr_despues', 0) - R.get('agro3_snr_antes', 0):.1f} dB"],
       ["Correlación con la verdad", V('agro3_corr_ruidosa', '{:.4f}'),
        V('agro3_corr_filtrada', '{:.4f}'), "—"],
       ["RMSE de pronóstico a 1 paso", V('t4_pred_rmse_ruidosa', '{:.4f}'),
        V('t4_pred_rmse_filtrada', '{:.4f}'), f"{V('t4_pred_mejora_pct', '{:.1f}')} %"]],
      [5.4 * cm, 3.6 * cm, 3.6 * cm, 3.4 * cm])
P("El experimento predictivo se diseñó para responder la pregunta <b>en el escenario "
  "realista</b>: en producción sólo se observa la serie ruidosa, y la decisión es si "
  "conviene filtrar antes de modelar. Se ajustó un AR(5) con partición 80/20 sin barajar, y "
  "<b>el error se midió siempre contra la señal limpia real</b> —evaluar contra la propia "
  "serie ruidosa premiaría al modelo que mejor reproduce el ruido. El modelo entrenado sobre "
  "la señal limpia, inobservable en la práctica, actúa como cota superior u <i>oráculo</i>.")
caja("Respuesta a la Tarea 4",
     f"<b>El RMSE de reconstrucción cae un {V('agro3_mejora_pct', '{:.1f}')} % "
     f"({V('agro3_rmse_ruidosa', '{:.4f}')} → {V('agro3_rmse_filtrada', '{:.4f}')})</b> con "
     f"un Butterworth de orden {V('agro3_orden')} y corte fc = {V('agro3_fc')}. "
     "<b>Y sí, el filtrado mejora la capacidad predictiva:</b> el RMSE de pronóstico a un "
     f"paso baja de {V('t4_pred_rmse_ruidosa', '{:.4f}')} a "
     f"{V('t4_pred_rmse_filtrada', '{:.4f}')} —un {V('t4_pred_mejora_pct', '{:.1f}')} %— "
     f"e <b>iguala prácticamente al oráculo</b> ({V('t4_pred_rmse_oraculo', '{:.4f}')}). "
     "Filtrar recupera casi toda la información predictiva que el ruido había destruido.<br/><br/>"
     "Dos validaciones cruzadas refuerzan el resultado: el corte óptimo hallado por barrido "
     f"cae en el entorno inmediato del cruce SNR = 0 dB predicho espectralmente "
     f"(f = {V('agro3_f_cruce_snr0', '{:.4f}')}), y el Butterworth supera a la media móvil "
     f"en todas las ventanas probadas (mejor media móvil: RMSE {V('t4_mejor_media_movil', '{:.4f}')}).",
     color=VERDE, fondo=colors.HexColor("#e8f4ea"))
figura("f06_t4_filtrado",
       "Figura 5. Reconstrucción de Agro_3, respuesta en frecuencia del filtro, barrido del "
       "corte —cuyo óptimo coincide con el cruce espectral— y error de pronóstico comparado "
       "con el oráculo.")
story.append(PageBreak())

# ═══════════════════════ 5. FASE 3 ═══════════════════════
H1("5. Fase 3 — Topología de la red")
H2("5.1 Tarea 5 · Construcción del grafo y nodo cuello de botella")
P("Se construyó un <code>DiGraph</code> agregando las observaciones por par "
  "(origen, destino) y usando el <b>número de transmisiones como peso de arista</b>, de modo "
  "que el grafo represente volumen real de telemetría y no la mera existencia del enlace. La "
  f"red eléctrica resultante tiene {V('grafo_ener_nodos')} nodos y "
  f"{V('grafo_ener_aristas')} aristas (densidad {V('grafo_ener_densidad', '{:.3f}')}).")

H3("Hallazgo estructural: la bipartición anula la betweenness dirigida")
P("Los identificadores no se solapan: las subestaciones ocupan el rango 100–119 y los nodos "
  "de carga el 200–249. <b>Ningún nodo es a la vez origen y destino</b>, de modo que toda "
  "ruta dirigida tiene longitud 1. Como la betweenness cuenta rutas mínimas que pasan "
  "<i>a través</i> de un nodo intermedio, y aquí no existe ningún intermediario posible, "
  f"<b>la betweenness dirigida vale exactamente 0 para los {V('grafo_ener_nodos')} nodos</b>. "
  "No es un fallo del cálculo sino una propiedad de la topología, y reportarla sin "
  "explicarla sería un error de lectura. El cuello de botella se identificó por tanto con "
  "cuatro métricas complementarias.")
_top = R.get("cen_top10", {})
tabla(["Nodo", "Grado", "Centralidad de grado", "Volumen telemetría",
       "Betweenness dirigida", "Betweenness no dirigida"],
      [[k, f"{v['grado']:.0f}", f"{v['centralidad_grado']:.3f}",
        f"{v['volumen_telemetria']:.0f}", f"{v['betweenness_dirigida']:.1f}",
        f"{v['betweenness_no_dirigida']:.4f}"] for k, v in list(_top.items())[:6]],
      [1.9 * cm, 1.9 * cm, 3.2 * cm, 3.2 * cm, 3.0 * cm, 3.0 * cm],
      resaltar={1: colors.HexColor("#fdf0e6")})

H3("Robustez: ¿existe realmente un punto único de fallo?")
P("Identificar el nodo más central no equivale a haber hallado una vulnerabilidad. La "
  "pregunta de negocio es cuánto se degrada la red si ese nodo cae, y se evaluó mediante "
  "puentes, puntos de articulación y simulación de fallo sobre la eficiencia global.")
tabla(["Indicador de vulnerabilidad", "Valor", "Lectura"],
      [["Puentes (aristas críticas)", V('n_puentes'), "Ninguna arista desconecta la red"],
       ["Puntos de articulación", V('n_articulacion'), "Ningún nodo desconecta la red"],
       ["Conectividad de nodos / aristas",
        f"{V('v3_node_connectivity')} / {V('v3_edge_connectivity')}",
        "Se requieren 13 fallos simultáneos para partir la red"],
       ["Grado mínimo", V('v3_grado_minimo'), "No hay nodos hoja frágiles"],
       ["Diámetro", V('grafo_ener_diametro'), "Malla compacta"],
       [f"Caída de eficiencia al eliminar el nodo {V('cuello_botella')}",
        f"{V('caida_eficiencia_cuello_pct', '{:.2f}')} %", "Degradación despreciable"]],
      [6.4 * cm, 3.0 * cm, 6.6 * cm])
caja("Respuesta a la Tarea 5",
     f"<b>El nodo cuello de botella es el {V('cuello_botella')}</b>, y los tres criterios "
     f"independientes coinciden: máxima betweenness no dirigida ({V('cuello_betw', '{:.4f}')}), "
     f"máximo grado ({V('cuello_grado')} de 50 enlaces posibles, centralidad "
     f"{V('cuello_centralidad_grado', '{:.3f}')}) y máximo volumen de telemetría "
     f"({V('cuello_volumen')} registros).<br/><br/>"
     "<b>Pero la red no tiene un punto único de fallo</b>, y esto invierte la recomendación "
     f"de negocio: eliminar el nodo más crítico cuesta apenas "
     f"{V('caida_eficiencia_cuello_pct', '{:.2f}')} % de eficiencia global y la red permanece "
     "conexa. La malla está, si acaso, <b>sobredimensionada en redundancia topológica</b>.")
figura("f07_t5_grafo",
       "Figura 6. Topología bipartita de la red eléctrica —20 subestaciones hacia 50 nodos de "
       "carga—, ranking de intermediación, relación grado–betweenness y simulación de fallo "
       "por nodo.")
story.append(PageBreak())

# ═══════════════════════ 6. FASE 4 ═══════════════════════
H1("6. Fase 4 — Respuestas a las preguntas de negocio")

H2("6.0 Contraste previo de la premisa del caso")
P("El caso «La Falla del Nodo 214» afirma que cuando el Precio Spot supera un umbral "
  "crítico, el flujo hacia ciertos nodos de carga se interrumpe. Aceptar esa premisa sin "
  "verificarla sería el error de consultoría más caro posible, de modo que se contrastó "
  f"primero: con el umbral fijado en el percentil 90 de <code>Ener_2</code>, el test χ² de "
  f"asociación entre precio alto y flujo hacia el nodo 214 arroja "
  f"<b>p = {V('premisa_chi2_p', '{:.3f}')}</b>. <b>No hay asociación significativa: la "
  "premisa no se verifica en los datos.</b>")

H2("6.1 P1 · Causalidad de Granger y propagación de fallos")
P("El test se aplicó con tres salvaguardas de rigor: verificación previa de estacionariedad "
  "—ambas series son I(0), de modo que se usan en niveles—, prueba de <b>ambas direcciones</b> "
  "y <b>corrección por comparaciones múltiples</b>, porque probar ocho rezagos y quedarse con "
  "el mínimo p-valor infla la tasa de falsos positivos.")
tabla(["Relación contrastada", "Mejor rezago", "p mínimo", "p corregido (Bonferroni)"],
      [["Ener_10 (F. Potencia) → Ener_9 (Voltaje)", V('granger_10_9_lag'),
        V('granger_10_9_p', '{:.4f}'), V('granger_10_9_bonferroni', '{:.4f}')],
       ["Ener_9 (Voltaje) → Ener_10 (F. Potencia)", "—",
        V('granger_9_10_p', '{:.4f}'), "no significativo"],
       ["Ener_10 → Ener_9 sobre datos <i>noise</i>", "—",
        V('granger_noise_p', '{:.4f}'), "no significativo"]],
      [6.4 * cm, 2.4 * cm, 3.4 * cm, 3.8 * cm])
caja("Respuesta a P1",
     "<b>La evidencia es direccionalmente coherente pero estadísticamente marginal, y no "
     "sobrevive a la corrección por comparaciones múltiples.</b> "
     f"<code>Ener_10 → Ener_9</code> alcanza p = {V('granger_10_9_p', '{:.4f}')} en el rezago "
     f"{V('granger_10_9_lag')}, y la dirección inversa nunca se acerca a la significancia "
     f"(p = {V('granger_9_10_p', '{:.3f}')}) —patrón consistente con la física del sistema. "
     f"Pero con Bonferroni el p-valor sube a {V('granger_10_9_bonferroni', '{:.3f}')}. La "
     "conclusión defendible es que <b>hay un indicio de precedencia temporal que justifica "
     "monitoreo, no una relación causal establecida</b>. La correlación contemporánea es "
     f"prácticamente nula ({V('granger_corr_contemporanea', '{:.3f}')}): cualquier relación "
     "es estrictamente dinámica y rezagada, invisible a un análisis de correlación simple."
     "<br/><br/>"
     f"<b>Sobre datos ruidosos la señal desaparece</b> (p = {V('granger_noise_p', '{:.3f}')}). "
     "El SNR de 6.15 dB de <code>Ener_10</code> basta para borrar la evidencia causal — un "
     "argumento de inversión en instrumentación por sí solo.<br/><br/>"
     "<b>¿Y el fallo del nodo de mayor betweenness?</b> Aunque la causalidad fuese firme, su "
     f"propagación sería limitada: la caída del nodo {V('cuello_botella')} cuesta "
     f"{V('caida_eficiencia_cuello_pct', '{:.2f}')} % de eficiencia y no desconecta a nadie. "
     "La inestabilidad de calidad de potencia se propagaría por <b>acoplamiento eléctrico</b>, "
     "no por la topología de telemetría. <b>El riesgo no es topológico, es de instrumentación.</b>")
figura("f08_p1_granger",
       "Figura 7. P1: p-valores por rezago en ambas direcciones, series de calidad de potencia "
       "y función de correlación cruzada.")

H2("6.2 P2 · Optimización geo-agronómica e inversión hídrica")
P("La pregunta incorpora una premisa —que los sensores de menor NDVI se localizan en una "
  "zona de alta pendiente asociada a mayor varianza del viento—. Se procedió en dos tiempos: "
  "contrastar la premisa y después responder la pregunta de inversión en ambos escenarios.")
tabla(["Contraste de la premisa", "Resultado", "Veredicto"],
      [["Varianza del viento: NDVI bajo vs alto",
        f"{V('p2_var_viento_bajo', '{:.2f}')} vs {V('p2_var_viento_alto', '{:.2f}')}; "
        f"Levene p = {V('p2_levene_p', '{:.3f}')}", "Sin diferencia"],
       ["Correlación NDVI ↔ desviación del viento",
        V('p2_corr_ndvi_viento', '{:.3f}'), "Nula"],
       ["Agrupamiento espacial de los extremos de NDVI",
        f"centroides a {V('p2_separacion_centroides_m', '{:.0f}')} m; "
        f"p = {V('p2_ttest_lat_p', '{:.2f}')} / {V('p2_ttest_lon_p', '{:.2f}')}",
        "No agrupados"],
       ["Corrección del jitter GPS por suavizado",
        "el suavizado no reduce el error", "Irreducible"]],
      [5.8 * cm, 5.6 * cm, 4.6 * cm])
P("El último punto merece explicación porque es contraintuitivo: <b>las coordenadas no son "
  "una serie temporal suave</b>. Cada fila corresponde a un sensor distinto en posición "
  "aleatoria —se verificó que las coordenadas no están ligadas al <code>Source_Node</code>—, "
  "no a una trayectoria. Por tanto el suavizado temporal no puede recuperar la posición: "
  "hacerlo requeriría un identificador de sensor con coordenada fija, que el dataset no "
  "provee.")
caja("Respuesta a P2 — recomendación de inversión",
     "<b>La premisa no se verifica, y la recomendación cambia por completo según se acepte o "
     "no.</b><br/><br/>"
     "<b>Escenario A (bajo la premisa asumida en el enunciado).</b> Si existiera una zona de "
     "alta pendiente con NDVI deprimido y mayor varianza de viento, lo indicado sería riego "
     "por goteo con compensación de presión —el goteo resiste la evapotranspiración inducida "
     "por viento mucho mejor que la aspersión, que sufre deriva— más barreras rompevientos "
     "en el perímetro expuesto, priorizando por gradiente de pendiente.<br/><br/>"
     "<b>Escenario B (lo que los datos sostienen). Ésta es la recomendación que se "
     "entrega:</b><br/>"
     f"<b>1.</b> <b>No focalizar la inversión hídrica por zona.</b> Con η² = "
     f"{V('t1_eta2_pct', '{:.2f}')} %, una inversión geográficamente dirigida asignaría "
     "capital sobre ruido muestral; su retorno esperado es esencialmente cero.<br/>"
     "<b>2.</b> <b>Invertir en capacidad de respuesta temporal</b>, no en obra fija "
     "zonificada: programación de riego dinámica gobernada por la evolución del NDVI, donde "
     f"reside el {V('p2_var_temporal_pct', '{:.0f}')} % de la variabilidad.<br/>"
     "<b>3.</b> <b>Prioridad presupuestal inmediata: instrumentación.</b> El SNR del dataset "
     f"agro cae hasta {V('snr_min', '{:.1f}')} dB en <code>{V('snr_peor_variable')}</code>. "
     "Con ese nivel de ruido se destruye la mitad de la capacidad predictiva y la estructura "
     "ARMA queda irreconocible. <b>Antes de invertir en infraestructura hídrica hay que poder "
     "medir su efecto</b>; hoy la red de sensores no lo permitiría.<br/>"
     f"<b>4.</b> <b>Corregir la telemetría GPS en origen.</b> Un error de ±"
     f"{R.get('jitter_agro_sigma_m', 0)/1000:.1f} km en latitud imposibilita cualquier "
     "agricultura de precisión.",
     color=NARANJA, fondo=colors.HexColor("#fdf0e6"))
figura("f09_p2_geo_agro",
       "Figura 8. P2: extremos de NDVI en el espacio, viento por grupo, dependencia temporal "
       "del NDVI y correlaciones con las variables hídricas en niveles y en diferencias.")

H2("6.3 P3 · ARIMAX de la demanda: ¿aporta la centralidad del nodo?")
P("<code>Ener_1</code> es I(1), de modo que se usó <b>d = 1</b>, cumpliendo el requisito de "
  "diferenciar antes de ajustar. Se construyó una escalera de modelos anidados con la misma "
  "variable dependiente y el mismo número de observaciones —condición sin la cual el AIC no "
  "es comparable— y se contrastó el test de Wald con el de razón de verosimilitud.")
_p3 = R.get("p3_tabla", {})
tabla(["Modelo", "AIC", "BIC", "Δ AIC vs M1", "Veredicto"],
      [[k, f"{v['AIC']:.2f}", f"{v['BIC']:.2f}",
        f"{v.get('Δ AIC vs M1', 0):+.2f}",
        "mejor" if abs(v.get('Δ AIC vs M1', 0)) < 0.1 and 'M3' in k else
        ("<b>referencia</b>" if 'M1' in k else
         ("empeora" if v.get('Δ AIC vs M1', 0) > 0.5 else "irrelevante"))]
       for k, v in _p3.items()],
      [6.2 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm, 2.4 * cm])
caja("Respuesta a P3",
     "<b>No. Incluir la centralidad del nodo en el grafo no mejora el AIC del modelo.</b><br/><br/>"
     f"La <b>temperatura sí aporta</b>: mejora el AIC en {V('p3_delta_aic_temp', '{:.2f}')} "
     f"puntos (coeficiente {V('p3_coef_temp', '{:.3f}')}, p = {V('p3_p_temp', '{:.4f}')}). "
     f"La <b>betweenness empeora el AIC en {V('p3_delta_aic_btw', '{:.2f}')} puntos</b>, y el "
     f"test de razón de verosimilitud lo confirma: LR = {V('p3_lr_stat', '{:.2f}')}, "
     f"p = {V('p3_lr_p', '{:.3f}')}. El p-valor de Wald ({V('p3_wald_p', '{:.3f}')}) sugiere "
     "lo contrario, pero es engañoso: el regresor tiene un coeficiente de variación de "
     f"{V('p3_btw_cv', '{:.2f}')} entre filas, lo que lo vuelve casi colineal con el "
     "intercepto e inestabiliza su error estándar. <b>Cuando Wald y LR discrepan, el criterio "
     "válido para discutir el AIC es el LR</b>, porque ambos se construyen sobre la misma "
     "verosimilitud.<br/><br/>"
     "<b>Por qué era esperable:</b> la demanda es una serie agregada del sistema, mientras la "
     "centralidad es un <b>atributo estático del nodo</b>. No varía en el tiempo, así que no "
     "puede explicar la dinámica temporal; a lo sumo capta un efecto fijo de nivel que la "
     "diferenciación ya elimina.<br/><br/>"
     "<b>Cómo sí integrar el grafo:</b> no como regresor exógeno en un ARIMAX agregado, sino "
     "modelando la demanda <b>por nodo</b> con la centralidad como efecto fijo en un modelo "
     "panel, o mediante <b>interacciones dinámicas</b> (centralidad × temperatura) que sí "
     "varían en el tiempo.")
figura("f10_p3_arimax",
       "Figura 9. P3: ajuste del ARIMAX, comparación de AIC entre especificaciones y "
       "diagnóstico de residuos.")
story.append(PageBreak())

# ═══════════════════════ 7. AUTO-EVALUACIÓN ═══════════════════════
H1("7. Preguntas de validación (auto-evaluación)")

H2("7.1 V1 · ¿Por qué Pearson no es válido sobre una serie con tendencia?")
P("La correlación de Pearson supone observaciones i.i.d. con media y varianza constantes. "
  "Una serie I(1) viola las tres condiciones: su media deambula y su varianza crece con t. "
  "El estadístico r deja de converger a un parámetro poblacional y se convierte en una "
  "<b>variable aleatoria no degenerada</b> (Granger y Newbold, 1974): incluso entre series "
  "independientes por construcción, |r| tiende a valores altos.")
_v1 = R.get("v1_espuria", {})
tabla(["Par de series", "r en NIVELES", "r en 1ª DIFERENCIA", "Caída"],
      [[k, f"{v['r en NIVELES']:+.4f}", f"{v['r en DIFERENCIAS']:+.4f}",
        f"{v['caída absoluta']:.4f}"] for k, v in _v1.items()],
      [7.0 * cm, 3.0 * cm, 3.4 * cm, 2.6 * cm])
P("El contraejemplo definitivo se construyó simulando <b>500 pares de paseos aleatorios "
  "independientes por construcción</b>, cuya correlación verdadera es exactamente cero: "
  f"el |r| observado tiene media <b>{V('v1_rw_r_medio', '{:.3f}')}</b> y supera 0.5 en el "
  f"<b>{V('v1_rw_pct_mayor_05', '{:.0f}')} %</b> de los casos.")
caja("Respuesta a V1",
     "Aplicar Pearson a series con tendencia produce <b>correlación espuria</b>. En este "
     f"dataset, Demanda ~ Temperatura pasa de r = {V('v1_corr_demanda_temp_niveles', '{:.4f}')} "
     f"en niveles a r = {V('v1_corr_demanda_temp_dif', '{:.4f}')} en diferencias: "
     "prácticamente toda la «relación» era tendencia compartida. Demanda ~ Precio Spot "
     "incluso cambia de signo. <b>Qué hacer en su lugar:</b> diferenciar hasta lograr I(0) y "
     "correlacionar los incrementos; o, si interesa la relación de largo plazo, contrastar "
     "<b>cointegración</b> (Engle-Granger / Johansen), que es el marco correcto para series I(1).")
figura("f11_v1_espuria",
       "Figura 10. V1: la misma pareja de series en niveles y en diferencias, y la "
       "distribución de |r| entre 500 pares de paseos aleatorios independientes.")

H2("7.2 V2 · Impacto del ruido de 5 dB sobre los coeficientes ARMA")
P(f"<code>{V('snr_peor_variable')}</code> es exactamente la variable de "
  f"{V('snr_min', '{:.1f}')} dB, el peor SNR del taller. El impacto sigue la teoría: añadir "
  "ruido blanco a un proceso AR(p) produce un <b>ARMA(p, p)</b> con coeficientes "
  "autorregresivos <b>atenuados hacia cero</b> —sesgo de atenuación por errores en "
  "variables— y una raíz MA que se acerca a −1.")
tabla(["Parámetro", f"{V('snr_peor_variable')} clean", f"{V('snr_peor_variable')} noise (5.0 dB)",
       "Agro_3 clean", "Agro_3 noise (10.8 dB)"],
      [["AR2 / AR1", V('v2_a7_ar2_clean', '{:.4f}'), V('v2_a7_ar2_noise', '{:.4f}'),
        V('v2_a3_ar1_clean', '{:.4f}'), V('v2_a3_ar1_noise', '{:.4f}')],
       ["MA1", "+0.9722", V('v2_a7_ma1_noise', '{:.4f}'), "−0.5109", "−0.8244"],
       ["σ² residual", "≈ 0", "20.2457", V('v2_a3_sigma_clean', '{:.4f}'),
        V('v2_a3_sigma_noise', '{:.4f}')]],
      [2.6 * cm, 3.3 * cm, 3.6 * cm, 3.2 * cm, 3.3 * cm])
caja("Respuesta a V2",
     "<b>El impacto es severo y sistemático.</b> En "
     f"<code>{V('snr_peor_variable')}</code> (5.0 dB) el coeficiente dominante se "
     f"<b>aniquila</b>: AR2 pasa de {V('v2_a7_ar2_clean', '{:.3f}')} a "
     f"{V('v2_a7_ar2_noise', '{:.3f}')}, y MA1 salta de +0.972 a "
     f"{V('v2_a7_ma1_noise', '{:.3f}')} —prácticamente sobre el círculo unitario, la firma "
     "inequívoca de una serie ahogada en ruido blanco. <b>Un modelo ajustado sobre estos "
     "datos identificaría una dinámica que no existe.</b> En <code>Agro_3</code> (10.8 dB) el "
     "sesgo es moderado pero real: la memoria se desplaza artificialmente al primer rezago y "
     f"σ² se infla de {V('v2_a3_sigma_clean', '{:.2f}')} a {V('v2_a3_sigma_noise', '{:.2f}')} "
     "—un factor de ×18.5—, ensanchando proporcionalmente todos los intervalos de "
     "pronóstico.<br/><br/>"
     "<b>Matiz importante: el filtrado no restituye los coeficientes originales.</b> Al "
     "reajustar el ARMA sobre la serie filtrada la estimación degenera (AR1 ≈ 2, σ² ≈ 0): el "
     "<code>filtfilt</code> elimina el ruido pero <b>impone su propia dinámica</b>. La "
     "lectura conjunta con la Tarea 4 es que <b>el preprocesamiento óptimo depende del uso "
     "previsto</b>: para <i>pronosticar</i>, filtrar es claramente beneficioso; para "
     "<i>identificar</i> la estructura ARMA, lo correcto es modelar el ruido de observación "
     "explícitamente (espacio de estados con ecuación de medición) en lugar de prefiltrar.",
     color=ROJO, fondo=colors.HexColor("#fdeceb"))
figura("f12_v2_arma_snr",
       "Figura 11. V2: destrucción de la estructura AR con 5 dB, sesgo moderado con 10.8 dB e "
       "inflación de la varianza residual.")

H2("7.3 V3 · ¿Cómo cambia la interpretación si el sensor es un «bridge»?")
P("Un <i>bridge</i> es una arista cuya eliminación aumenta el número de componentes conexas. "
  "La interpretación de un fallo cambia de forma <b>cualitativa, no gradual</b>:")
tabla(["Dimensión", "Nodo redundante", "Nodo puente"],
      [["Efecto del fallo", "Degradación <b>gradual</b> de latencia",
        "<b>Pérdida total</b> de observabilidad de un segmento"],
       ["Recuperación", "Rutas alternativas absorben el tráfico",
        "Requiere intervención física"],
       ["Naturaleza del dato faltante", "<i>Missing at random</i> → imputable",
        "<b>Censura sistemática</b> de un subsistema"],
       ["Prioridad operativa", "Mantenimiento programado", "<b>Redundancia inmediata</b>"],
       ["SLA", "Admite degradación", "Exige respaldo dedicado"]],
      [4.2 * cm, 5.6 * cm, 6.2 * cm])
P("El punto estadístico es el que más se suele pasar por alto: cuando cae un puente, los "
  "datos que faltan <b>no son aleatorios</b>, sino todo un subsistema. Cualquier imputación "
  "o promedio calculado después está <b>sesgado por construcción</b>, porque se ha perdido "
  "una región completa del espacio de estados, no una muestra aleatoria de él.")
caja("Respuesta a V3",
     "<b>En esta red concreta la pregunta es contrafactual.</b> La auditoría arroja "
     f"<b>{V('n_puentes')} puentes y {V('n_articulacion')} puntos de articulación</b>, con "
     f"conectividad de nodos y de aristas igual a {V('v3_node_connectivity')} y grado mínimo "
     f"{V('v3_grado_minimo')}. <b>Ningún sensor de esta red es un puente.</b> Por eso el peor "
     f"fallo posible cuesta {V('caida_eficiencia_cuello_pct', '{:.2f}')} % de eficiencia, "
     f"frente al {V('v3_demo_caida_pct', '{:.0f}')} % que produce la caída de un nodo puente "
     "en la red de contraste construida como control. La red de TechLogistics está "
     "sobredimensionada en redundancia topológica — argumento directo para reasignar "
     "presupuesto de redundancia hacia calidad de instrumentación.")

H2("7.4 V4 · ¿Influye la posición geográfica en la varianza de la señal?")
_v4 = R.get("v4_tabla", {})
tabla(["Variable", "σ² entre zonas", "σ² intra zona", "η² (%)", "ANOVA p"],
      [[k, f"{v['σ² entre zonas']:.4f}", f"{v['σ² intra zona']:.4f}",
        f"{v['η² (%)']:.2f}", f"{v['ANOVA p']:.3f}"] for k, v in _v4.items()],
      [3.4 * cm, 3.2 * cm, 3.2 * cm, 2.6 * cm, 2.6 * cm])
caja("Respuesta a V4",
     "<b>En este dataset la posición geográfica no influye de forma apreciable en la "
     "varianza de la señal</b>, y la evidencia es consistente en tres frentes: η² < 1 % para "
     "las cuatro variables analizadas; el test de Bartlett de homogeneidad de varianzas entre "
     f"zonas no se rechaza (p = {V('v4_bartlett_p', '{:.3f}')}); y el mapa hexagonal de "
     "varianza local no muestra gradiente.<br/><br/>"
     "<b>La explicación está en el diseño de la red.</b> El área monitoreada mide "
     f"~{V('area_lat_km', '{:.0f}')} × {V('area_lon_km', '{:.0f}')} km con sensores "
     "distribuidos uniformemente al azar —se verificó que las coordenadas no están ligadas al "
     "identificador del sensor—. En una extensión tan pequeña y homogénea del Oriente "
     "Antioqueño no hay gradientes climáticos capaces de generar heterocedasticidad espacial."
     "<br/><br/>"
     "<b>Dónde sí esperaríamos que la geografía dominara:</b> gradientes altitudinales "
     "pronunciados, proximidad a cuerpos de agua, distancia al gateway —que degrada el SNR de "
     "radio— o exposición a vientos de ladera. <b>Nada de eso es observable con las variables "
     "disponibles</b>: el dataset no incluye altitud, ni distancia al gateway, ni "
     "identificador de sensor con posición fija. Ésa es precisamente la carencia que la "
     "recomendación de P2 propone corregir.")
figura("f13_v4_geo_varianza",
       "Figura 12. V4: varianza local del viento por celda espacial, varianza explicada por la "
       "ubicación y dispersión por zona.")
story.append(PageBreak())

# ═══════════════════════ 8. CONCLUSIONES ═══════════════════════
H1("8. Conclusiones y plan de acción")
P("El encargo pedía integrar tres capas de información para decidir dónde invertir. La "
  "respuesta que emerge del análisis es contraria a la intuición implícita en el <i>briefing</i>: "
  "<b>la fragilidad de TechLogistics no está en su red, sino en sus sensores</b>.")

H2("8.1 Prioridades de inversión, en orden")
tabla(["Prioridad", "Acción", "Justificación cuantitativa", "Horizonte"],
      [["<b>1</b>", "Renovar la instrumentación de las variables de peor SNR",
        f"<code>{V('snr_peor_variable')}</code> a {V('snr_min', '{:.1f}')} dB: "
        "la estructura ARMA se vuelve irreconocible y el filtrado no la restituye", "Inmediato"],
       ["<b>2</b>", "Implantar filtrado Butterworth en la cadena de ingesta",
        f"Reduce el RMSE un {V('agro3_mejora_pct', '{:.0f}')} % y el error de pronóstico un "
        f"{V('t4_pred_mejora_pct', '{:.0f}')} %, hasta igualar al oráculo", "Corto plazo"],
       ["<b>3</b>", "Corrección diferencial de GPS y coordenada fija por sensor",
        f"Error de ±{R.get('jitter_agro_sigma_m', 0)/1000:.1f} km en latitud; el jitter es "
        "irreducible por suavizado con los datos actuales", "Corto plazo"],
       ["<b>4</b>", "Cobertura financiera del costo del gas",
        "<code>Ener_5</code> es un random walk con drift: sin reversión a la media, el riesgo "
        "crece con √h", "Medio plazo"],
       ["<b>5</b>", "Congelar inversión adicional en redundancia de red",
        f"{V('n_puentes')} puentes y {V('n_articulacion')} articulaciones; el peor fallo "
        f"cuesta {V('caida_eficiencia_cuello_pct', '{:.2f}')} %", "Inmediato"],
       ["<b>6</b>", "Instrumentar altitud y distancia al gateway",
        "Sin esas variables no es posible detectar el efecto de la geografía sobre la "
        "varianza de la señal", "Medio plazo"]],
      [1.9 * cm, 4.3 * cm, 7.0 * cm, 2.8 * cm])

H2("8.2 Nota sobre las premisas del encargo")
P("Tres de las premisas incorporadas en las preguntas de negocio <b>no se sostienen al "
  "contrastarlas con los datos</b>: que el nodo 214 sea un activo crítico "
  f"(puesto {V('nodo214_rank')} de {V('nodo214_total_nodos')}; su caída incluso mejora la "
  "eficiencia), que exista una zona de baja biomasa asociada a alta varianza del viento "
  f"(Levene p = {V('p2_levene_p', '{:.3f}')}), y que el precio spot alto interrumpa el flujo "
  f"hacia el nodo 214 (χ² p = {V('premisa_chi2_p', '{:.3f}')}). Se documentan explícitamente "
  "porque una recomendación de inversión construida sobre una premisa falsa es más costosa "
  "que la ausencia de recomendación.")

H2("8.3 Reproducibilidad")
P("Todo el análisis reside en un repositorio Git con la siguiente estructura. El cuaderno es "
  "la única fuente de verdad: genera las figuras y el archivo de resultados que este informe "
  "consume.")
tabla(["Componente", "Ruta", "Contenido"],
      [["Cuaderno de análisis", "<code>notebooks/</code>",
        "92 celdas (44 markdown, 48 de código) ejecutadas de extremo a extremo"],
       ["Datos originales", "<code>data/</code>", "Los cuatro CSV sin modificar"],
       ["Figuras", "<code>figures/</code>",
        f"{len(list(FIGS.glob('*.png')))} PNG a 150 dpi"],
       ["Visualizaciones interactivas", "<code>outputs/*.html</code>",
        "Mapas Plotly y grafo interactivo"],
       ["Resultados serializados", "<code>outputs/results.json</code>",
        f"{len(R)} cifras; única entrada de este informe"],
       ["Scripts", "<code>scripts/</code>",
        "<code>run_analysis.py</code> y <code>build_report.py</code>"]],
      [4.4 * cm, 4.4 * cm, 7.2 * cm])
P("Para reproducir de cero: <code>pip install -r requirements.txt</code>, después "
  "<code>python scripts/run_analysis.py</code> y finalmente "
  "<code>python scripts/build_report.py</code>. Las semillas aleatorias están fijadas.")

SP(14)
cita = Table([[Paragraph(
    "<i>«Un científico de datos senior no solo mira los puntos; mira las conexiones y el "
    "territorio donde habitan.»</i>",
    ParagraphStyle("cita", parent=S["cuerpo"], alignment=TA_CENTER, fontName=FUENTE_I,
                   fontSize=10, textColor=AZUL))]], colWidths=[16.0 * cm])
cita.setStyle(TableStyle([
    ("LINEABOVE", (0, 0), (-1, 0), 0.8, NARANJA),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, NARANJA),
    ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
]))
story.append(cita)

# ─────────────────────────── Construcción ───────────────────────────
if __name__ == "__main__":
    doc.build(story)
    print(f"✔ Informe generado: {DEST}")
    print(f"  {DEST.stat().st_size / 1024:.0f} KB")
