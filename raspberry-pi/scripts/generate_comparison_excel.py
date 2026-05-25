#!/usr/bin/env python3
"""
Genera un Excel comparativo a partir de dos sesiones de evaluación (noaug vs aug).

Hojas generadas:
  1. Datos Brutos              — todos los eventos con true_name y clasificación
  2. Resumen Global            — tasa de reconocimiento + gráficas
  3. Por Persona               — métricas por persona + gráfica de similitud
  4. Distribución Similitudes  — valores individuales para scatter/box
  5. Métricas Clasificación    — TP/FP/FN/TN, precisión, recall, F1, FAR, FRR
  6. Curva ROC                 — ROC a 100 umbrales + gráfica AUC

Uso:
    python scripts/generate_comparison_excel.py \
        --noaug  <ruta/sesion_noag.csv> \
        --aug    <ruta/sesion_ag.csv>   \
        --output <ruta/comparacion.xlsx>

Ejemplo Windows:
    python scripts/generate_comparison_excel.py \
        --noaug  "D:/Descargas/sesion_noag.csv" \
        --aug    "D:/Descargas/sesion_ag.csv"   \
        --output "D:/Descargas/comparacion_sesiones.xlsx"

Requisito: openpyxl  (pip install openpyxl)
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# ── Colores ────────────────────────────────────────────────────────────────
COLOR_NOAUG  = "4472C4"   # azul  — sin augmentación
COLOR_AUG    = "ED7D31"   # naranja — con augmentación
COLOR_HEADER = "2F4F7F"   # azul oscuro para cabeceras
COLOR_ALT    = "EEF2FF"   # fila alternada

LABEL_NOAUG = "Sin Augmentación"
LABEL_AUG   = "Con Augmentación"

# ── Anotaciones (event_id → true_name) ────────────────────────────────────
# Sesión del 18/05/2026 — rellenadas a partir del recuerdo del usuario.
# "Impostor" = persona NO inscrita en la DB.
# La detección "Concana" a las 13:49:21 en aug (sim=0.3142) era persona no
# inscrita → FP.

ANNOTATIONS_NOAUG: dict[str, str] = {
    # Mark reconocido correctamente (TP)
    "3076ded7": "Mark",    "ec796211": "Mark",    "615a1205": "Mark",
    "46af353c": "Mark",    "ac2b68d3": "Mark",    "d78c25cd": "Mark",    "9d549169": "Mark",
    # Personas no inscritas
    "206b9763": "Impostor", "eae3d8bd": "Impostor", "b6462744": "Impostor",
    "2ea4942e": "Impostor", "5f5c0270": "Impostor", "82468a4c": "Impostor",
    "933bff53": "Impostor", "482c62e7": "Impostor", "3a769a1d": "Impostor",
    "ce8fe992": "Impostor", "d55bfcc0": "Impostor", "97ac168e": "Impostor",
    "fcd2849c": "Impostor", "0e7dbd50": "Impostor", "e1f202e9": "Impostor",
    # Concana reconocida correctamente (TP)
    "19bbb0c4": "Concana",  "9bfd17fe": "Concana",
    "1a23e6d6": "Concana",  "6c987303": "Concana",
    # Mario reconocido correctamente (TP)
    "7c556ab4": "Mario",    "4cae8f54": "Mario",
    "cdaf44cd": "Mario",    "ee382487": "Mario",
}

ANNOTATIONS_AUG: dict[str, str] = {
    # Personas no inscritas (13:49 y 13:52)
    "eead85d1": "Impostor", "36d56574": "Impostor",
    "12eec5b9": "Impostor",   # predicho "Concana" pero era impostor → FP
    "db72a5e5": "Impostor",   "a60dc5c1": "Impostor",
    "52f8f7d8": "Impostor",   "285d9c3d": "Impostor",   "6904eb82": "Impostor",
    "3bf6a11e": "Impostor",   "8fa8ced2": "Impostor",   "1103d1cc": "Impostor",
    "090fb24b": "Impostor",   "a0be2587": "Impostor",   "e265d0fc": "Impostor",
    # Mario reconocido correctamente (TP)
    "dc933dba": "Mario",  "0f07462f": "Mario",  "e5f57a71": "Mario",
    "22542631": "Mario",  "d9aeb065": "Mario",  "978c0b2d": "Mario",  "83e73e7f": "Mario",
    # Concana reconocida correctamente (TP)
    "a75b8934": "Concana",  "883719b5": "Concana",
    "a6bc0a08": "Concana",  "40db71ee": "Concana",
}


# ── Helpers de estilo ──────────────────────────────────────────────────────

def _header_cell(ws, row: int, col: int, value) -> None:
    cell = ws.cell(row=row, column=col, value=value)
    cell.fill = PatternFill("solid", fgColor=COLOR_HEADER)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.alignment = Alignment(horizontal="center", vertical="center")


def _header_row(ws, row: int, values: list) -> None:
    for col, val in enumerate(values, start=1):
        _header_cell(ws, row, col, val)


def _auto_width(ws, max_width: int = 30) -> None:
    for col_cells in ws.columns:
        width = max(len(str(c.value or "")) for c in col_cells)
        letter = get_column_letter(col_cells[0].column)
        ws.column_dimensions[letter].width = min(width + 2, max_width)


def _pct(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


# ── Carga de CSVs con anotaciones ─────────────────────────────────────────

def load_csv(path: Path, db_mode: str, annotations: dict[str, str]) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            event_id  = row["event_id"]
            true_name = row.get("true_name", "").strip() or annotations.get(event_id, "")
            rows.append({
                "timestamp":      row["timestamp"],
                "event_id":       event_id,
                "predicted_name": row["predicted_name"],
                "similarity":     float(row["similarity"]),
                "matched":        int(row["matched"]),
                "threshold_used": float(row["threshold_used"]),
                "true_name":      true_name,
                "notes":          row.get("notes", ""),
                "db_mode":        db_mode,
            })
    return rows


# ── Clasificación TP / FP / FN / TN ───────────────────────────────────────

def _classify(row: dict) -> str:
    true    = row["true_name"]
    pred    = row["predicted_name"]
    matched = row["matched"]
    if not true:
        return ""
    impostor = (true == "Impostor")
    if matched == 1 and not impostor and pred == true:
        return "TP"
    if matched == 1 and (impostor or pred != true):
        return "FP"
    if matched == 0 and not impostor:
        return "FN"
    if matched == 0 and impostor:
        return "TN"
    return ""


# ── Cómputo de curva ROC ──────────────────────────────────────────────────

def _compute_roc(rows: list[dict]) -> list[dict]:
    annotated = [r for r in rows if r["true_name"]]
    if not annotated:
        return []
    y_true  = [0 if r["true_name"] == "Impostor" else 1 for r in annotated]
    y_score = [r["similarity"] for r in annotated]
    total_p = sum(y_true)
    total_n = len(y_true) - total_p
    points  = []
    for i in range(101):
        thresh = round(i / 100, 2)
        tp = sum(1 for yt, ys in zip(y_true, y_score) if yt == 1 and ys >= thresh)
        fp = sum(1 for yt, ys in zip(y_true, y_score) if yt == 0 and ys >= thresh)
        fn = total_p - tp
        tn = total_n - fp
        points.append({
            "threshold": thresh,
            "TPR": _pct(tp, total_p),
            "FPR": _pct(fp, total_n),
            "FAR": _pct(fp, total_n),
            "FRR": _pct(fn, total_p) if total_p else 0.0,
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        })
    return points


def _auc(roc: list[dict]) -> float:
    if not roc:
        return 0.0
    pts  = sorted(roc, key=lambda x: x["FPR"])
    area = 0.0
    for i in range(1, len(pts)):
        dx    = pts[i]["FPR"] - pts[i - 1]["FPR"]
        dy    = (pts[i]["TPR"] + pts[i - 1]["TPR"]) / 2
        area += dx * dy
    return round(area, 4)


def _eer(roc: list[dict]) -> float:
    if not roc:
        return 0.0
    best = min(roc, key=lambda x: abs(x["FAR"] - x["FRR"]))
    return round((best["FAR"] + best["FRR"]) / 2, 4)


# ── Hoja 1: Datos Brutos ───────────────────────────────────────────────────

def sheet_raw_data(wb: Workbook, all_rows: list[dict]) -> None:
    ws = wb.active
    ws.title = "Datos Brutos"
    ws.row_dimensions[1].height = 20

    headers = [
        "timestamp", "event_id", "predicted_name", "similarity",
        "matched", "threshold_used", "true_name", "clasificacion", "db_mode",
    ]
    _header_row(ws, 1, headers)

    clf_colors = {
        "TP": "C6EFCE", "FP": "FFC7CE",
        "FN": "FFEB9C", "TN": "DDEBF7",
    }
    alt = PatternFill("solid", fgColor=COLOR_ALT)
    for i, row in enumerate(all_rows, start=2):
        clf  = _classify(row)
        vals = [
            row["timestamp"], row["event_id"], row["predicted_name"],
            row["similarity"], row["matched"], row["threshold_used"],
            row["true_name"], clf, row["db_mode"],
        ]
        for col, val in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if clf in clf_colors:
                cell.fill = PatternFill("solid", fgColor=clf_colors[clf])
            elif i % 2 == 0:
                cell.fill = alt

    _auto_width(ws)


# ── Hoja 2: Resumen Global ────────────────────────────────────────────────

def sheet_global_summary(wb: Workbook, noaug: list[dict], aug: list[dict]) -> None:
    ws = wb.create_sheet("Resumen Global")
    ws.row_dimensions[1].height = 20

    def _stats(rows):
        total    = len(rows)
        matched  = sum(1 for r in rows if r["matched"] == 1)
        sims     = [r["similarity"] for r in rows if r["matched"] == 1]
        return {
            "total":        total,
            "matched":      matched,
            "unmatched":    total - matched,
            "match_pct":    round(matched / total * 100, 1) if total else 0.0,
            "mean_sim":     round(mean(sims), 4) if sims else None,
            "max_sim":      round(max(sims), 4) if sims else None,
        }

    sn = _stats(noaug)
    sa = _stats(aug)

    headers = [
        "DB Mode", "Total Eventos", "Reconocidos", "No Reconocidos",
        "Tasa Reconocimiento (%)", "Sim Media (reconocidos)", "Sim Máx (reconocidos)",
    ]
    _header_row(ws, 1, headers)

    rows_data = [
        [LABEL_NOAUG, sn["total"], sn["matched"], sn["unmatched"], sn["match_pct"], sn["mean_sim"], sn["max_sim"]],
        [LABEL_AUG,   sa["total"], sa["matched"], sa["unmatched"], sa["match_pct"], sa["mean_sim"], sa["max_sim"]],
    ]
    for i, rd in enumerate(rows_data, start=2):
        for col, val in enumerate(rd, start=1):
            ws.cell(row=i, column=col, value=val)

    _auto_width(ws)

    # ── Gráfica 1: Reconocidos vs No Reconocidos ────────────────────────
    chart1 = BarChart()
    chart1.type = "col"
    chart1.grouping = "clustered"
    chart1.title = "Reconocidos vs No Reconocidos"
    chart1.y_axis.title = "Nº Eventos"
    chart1.x_axis.title = "Base de datos"

    data_ref = Reference(ws, min_col=3, max_col=4, min_row=1, max_row=3)
    cats     = Reference(ws, min_col=1, min_row=2, max_row=3)
    chart1.add_data(data_ref, titles_from_data=True)
    chart1.set_categories(cats)
    chart1.series[0].graphicalProperties.solidFill = COLOR_NOAUG
    chart1.series[1].graphicalProperties.solidFill = "FF0000"   # rojo = no reconocidos
    chart1.width = 14
    chart1.height = 11
    ws.add_chart(chart1, "I2")

    # ── Gráfica 2: Tasa de Reconocimiento ───────────────────────────────
    chart2 = BarChart()
    chart2.type = "col"
    chart2.grouping = "clustered"
    chart2.title = "Tasa de Reconocimiento (%)"
    chart2.y_axis.title = "%"
    chart2.y_axis.scaling.min = 0
    chart2.y_axis.scaling.max = 100

    rate_ref = Reference(ws, min_col=5, max_col=5, min_row=1, max_row=3)
    chart2.add_data(rate_ref, titles_from_data=True)
    chart2.set_categories(cats)
    chart2.series[0].graphicalProperties.solidFill = COLOR_NOAUG
    chart2.width = 12
    chart2.height = 11
    ws.add_chart(chart2, "I22")

    # ── Gráfica 3: Similitud Media ───────────────────────────────────────
    chart3 = BarChart()
    chart3.type = "col"
    chart3.grouping = "clustered"
    chart3.title = "Similitud Media (eventos reconocidos)"
    chart3.y_axis.title = "Similitud Coseno"
    chart3.y_axis.scaling.min = 0
    chart3.y_axis.scaling.max = 1.0

    sim_ref = Reference(ws, min_col=6, max_col=6, min_row=1, max_row=3)
    chart3.add_data(sim_ref, titles_from_data=True)
    chart3.set_categories(cats)
    chart3.series[0].graphicalProperties.solidFill = COLOR_AUG
    chart3.width = 12
    chart3.height = 11
    ws.add_chart(chart3, "I42")


# ── Hoja 3: Por Persona ───────────────────────────────────────────────────

def sheet_per_person(wb: Workbook, noaug: list[dict], aug: list[dict]) -> None:
    ws = wb.create_sheet("Por Persona")
    ws.row_dimensions[1].height = 20

    def _person_sims(rows) -> dict[str, list[float]]:
        d: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            if r["matched"] == 1:
                d[r["predicted_name"]].append(r["similarity"])
        return d

    sims_noaug = _person_sims(noaug)
    sims_aug   = _person_sims(aug)
    all_people = sorted(set(list(sims_noaug) + list(sims_aug)))

    headers = [
        "Persona",
        f"Eventos ({LABEL_NOAUG})",
        f"Sim Media ({LABEL_NOAUG})",
        f"Sim Máx ({LABEL_NOAUG})",
        f"Sim Mín ({LABEL_NOAUG})",
        f"Eventos ({LABEL_AUG})",
        f"Sim Media ({LABEL_AUG})",
        f"Sim Máx ({LABEL_AUG})",
        f"Sim Mín ({LABEL_AUG})",
    ]
    _header_row(ws, 1, headers)

    alt = PatternFill("solid", fgColor=COLOR_ALT)
    for i, person in enumerate(all_people, start=2):
        n = sims_noaug.get(person, [])
        a = sims_aug.get(person, [])
        row_vals = [
            person,
            len(n), round(mean(n), 4) if n else None, round(max(n), 4) if n else None, round(min(n), 4) if n else None,
            len(a), round(mean(a), 4) if a else None, round(max(a), 4) if a else None, round(min(a), 4) if a else None,
        ]
        for col, val in enumerate(row_vals, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if i % 2 == 0:
                cell.fill = alt

    _auto_width(ws)

    # ── Tabla auxiliar para la gráfica (solo valores numéricos) ─────────
    chart_row = len(all_people) + 4
    ws.cell(row=chart_row, column=1, value="Persona")
    ws.cell(row=chart_row, column=2, value=LABEL_NOAUG)
    ws.cell(row=chart_row, column=3, value=LABEL_AUG)

    for offset, person in enumerate(all_people):
        n = sims_noaug.get(person, [])
        a = sims_aug.get(person, [])
        ws.cell(row=chart_row + 1 + offset, column=1, value=person)
        ws.cell(row=chart_row + 1 + offset, column=2, value=round(mean(n), 4) if n else None)
        ws.cell(row=chart_row + 1 + offset, column=3, value=round(mean(a), 4) if a else None)

    last_data_row = chart_row + len(all_people)

    # ── Gráfica: Similitud Media por Persona ────────────────────────────
    chart = BarChart()
    chart.type = "col"
    chart.grouping = "clustered"
    chart.title = "Similitud Media por Persona"
    chart.y_axis.title = "Similitud Coseno"
    chart.y_axis.scaling.min = 0
    chart.y_axis.scaling.max = 1.0
    chart.x_axis.title = "Persona"

    data_ref = Reference(ws, min_col=2, max_col=3, min_row=chart_row, max_row=last_data_row)
    cats     = Reference(ws, min_col=1, min_row=chart_row + 1, max_row=last_data_row)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats)
    chart.series[0].graphicalProperties.solidFill = COLOR_NOAUG
    chart.series[1].graphicalProperties.solidFill = COLOR_AUG
    chart.width = 20
    chart.height = 14
    ws.add_chart(chart, "K2")


# ── Hoja 4: Distribución Similitudes ─────────────────────────────────────

def sheet_distribution(wb: Workbook, noaug: list[dict], aug: list[dict]) -> None:
    """
    Una fila por evento reconocido (matched=1).
    Útil para construir scatter plots o box plots en Excel / Power BI.
    """
    ws = wb.create_sheet("Distribución Similitudes")
    ws.row_dimensions[1].height = 20

    headers = ["Persona", "DB Mode", "Similitud", "Clasificación"]
    _header_row(ws, 1, headers)

    alt = PatternFill("solid", fgColor=COLOR_ALT)
    row_num = 2
    for r in noaug + aug:
        if r["matched"] == 1:
            clf = _classify(r)
            ws.cell(row=row_num, column=1, value=r["predicted_name"])
            ws.cell(row=row_num, column=2, value=r["db_mode"])
            ws.cell(row=row_num, column=3, value=r["similarity"])
            ws.cell(row=row_num, column=4, value=clf)
            if row_num % 2 == 0:
                for col in range(1, 5):
                    ws.cell(row=row_num, column=col).fill = alt
            row_num += 1

    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 14


# ── Hoja 5: Métricas de Clasificación ─────────────────────────────────────

def sheet_classification(wb: Workbook, noaug: list[dict], aug: list[dict]) -> None:
    ws = wb.create_sheet("Métricas Clasificación")

    def _summary(rows, label):
        counts = defaultdict(int)
        for r in rows:
            c = _classify(r)
            if c:
                counts[c] += 1
        tp = counts["TP"]; fp = counts["FP"]
        fn = counts["FN"]; tn = counts["TN"]
        total     = tp + fp + fn + tn
        precision = _pct(tp, tp + fp)
        recall    = _pct(tp, tp + fn)
        f1        = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0
        accuracy  = _pct(tp + tn, total)
        far       = _pct(fp, fp + tn)
        frr       = _pct(fn, fn + tp)
        return [label, tp, fp, fn, tn, precision, recall, f1, accuracy, far, frr]

    ws.cell(row=1, column=1, value="Resumen de Clasificación (umbral = 0.30)").font = Font(bold=True, size=12)
    ws.merge_cells("A1:K1")

    headers = ["DB Mode", "TP", "FP", "FN", "TN",
               "Precisión", "Recall", "F1-Score", "Accuracy", "FAR", "FRR"]
    _header_row(ws, 2, headers)

    for i, data in enumerate([_summary(noaug, LABEL_NOAUG), _summary(aug, LABEL_AUG)], start=3):
        for col, val in enumerate(data, start=1):
            ws.cell(row=i, column=col, value=val)

    _auto_width(ws)

    # ── Tabla por persona ────────────────────────────────────────────────
    ws.cell(row=6, column=1, value="Desglose por Persona").font = Font(bold=True, size=11)
    _header_row(ws, 7, ["Persona", "DB Mode", "TP", "FP", "FN", "Precisión", "Recall", "F1-Score"])

    def _per_person(rows, label):
        by: dict[str, dict] = defaultdict(lambda: defaultdict(int))
        for r in rows:
            clf = _classify(r)
            if not clf:
                continue
            person = r["true_name"] if clf in ("TP", "FN") else r["predicted_name"]
            if person != "Impostor":
                by[person][clf] += 1
        out = []
        for person in sorted(by):
            d = by[person]
            tp = d["TP"]; fp = d["FP"]; fn = d["FN"]
            prec = _pct(tp, tp + fp)
            rec  = _pct(tp, tp + fn)
            f1   = round(2 * prec * rec / (prec + rec), 4) if (prec + rec) else 0.0
            out.append([person, label, tp, fp, fn, prec, rec, f1])
        return out

    alt = PatternFill("solid", fgColor=COLOR_ALT)
    all_p = _per_person(noaug, LABEL_NOAUG) + _per_person(aug, LABEL_AUG)
    for i, rd in enumerate(all_p, start=8):
        for col, val in enumerate(rd, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if i % 2 == 0:
                cell.fill = alt

    # ── Gráfica TP/FP/FN ────────────────────────────────────────────────
    cats = Reference(ws, min_col=1, min_row=3, max_row=4)
    bar1 = BarChart()
    bar1.type = "col"; bar1.grouping = "clustered"
    bar1.title = "TP / FP / FN por Sesión"
    bar1.y_axis.title = "Eventos"
    bar1.add_data(Reference(ws, min_col=2, max_col=4, min_row=2, max_row=4), titles_from_data=True)
    bar1.set_categories(cats)
    bar1.series[0].graphicalProperties.solidFill = "70AD47"
    bar1.series[1].graphicalProperties.solidFill = "FF0000"
    bar1.series[2].graphicalProperties.solidFill = "FFC000"
    bar1.width = 14; bar1.height = 11
    ws.add_chart(bar1, "M2")

    bar2 = BarChart()
    bar2.type = "col"; bar2.grouping = "clustered"
    bar2.title = "Precisión / Recall / F1"
    bar2.y_axis.title = "Valor [0–1]"
    bar2.y_axis.scaling.min = 0; bar2.y_axis.scaling.max = 1.0
    bar2.add_data(Reference(ws, min_col=6, max_col=8, min_row=2, max_row=4), titles_from_data=True)
    bar2.set_categories(cats)
    bar2.series[0].graphicalProperties.solidFill = COLOR_NOAUG
    bar2.series[1].graphicalProperties.solidFill = COLOR_AUG
    bar2.series[2].graphicalProperties.solidFill = "A9D18E"
    bar2.width = 14; bar2.height = 11
    ws.add_chart(bar2, "M22")


# ── Hoja 6: Curva ROC ─────────────────────────────────────────────────────

def sheet_roc(wb: Workbook, noaug: list[dict], aug: list[dict]) -> None:
    ws = wb.create_sheet("Curva ROC")

    roc_n = _compute_roc(noaug)
    roc_a = _compute_roc(aug)
    auc_n = _auc(roc_n);  auc_a = _auc(roc_a)
    eer_n = _eer(roc_n);  eer_a = _eer(roc_a)
    n     = len(roc_n)

    headers = [
        "Umbral",
        f"FPR ({LABEL_NOAUG})", f"TPR ({LABEL_NOAUG})",
        f"FAR ({LABEL_NOAUG})", f"FRR ({LABEL_NOAUG})",
        f"FPR ({LABEL_AUG})",   f"TPR ({LABEL_AUG})",
        f"FAR ({LABEL_AUG})",   f"FRR ({LABEL_AUG})",
    ]
    _header_row(ws, 1, headers)

    alt = PatternFill("solid", fgColor=COLOR_ALT)
    for i, (rn, ra) in enumerate(zip(roc_n, roc_a), start=2):
        vals = [rn["threshold"],
                rn["FPR"], rn["TPR"], rn["FAR"], rn["FRR"],
                ra["FPR"], ra["TPR"], ra["FAR"], ra["FRR"]]
        for col, val in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if i % 2 == 0:
                cell.fill = alt

    _auto_width(ws)
    last = 1 + n

    # ── Gráfica ROC ──────────────────────────────────────────────────────
    ch_roc = ScatterChart()
    ch_roc.scatterStyle = "lineMarker"   # une los puntos con línea
    ch_roc.title  = f"Curva ROC  (AUC noaug={auc_n}  |  AUC aug={auc_a})"
    ch_roc.style  = 10
    ch_roc.x_axis.title = "FPR (1 − Especificidad)"
    ch_roc.y_axis.title = "TPR (Sensibilidad)"
    ch_roc.x_axis.scaling.min = 0; ch_roc.x_axis.scaling.max = 1
    ch_roc.y_axis.scaling.min = 0; ch_roc.y_axis.scaling.max = 1

    for x_col, y_col, label, color in [
        (2, 3, f"{LABEL_NOAUG} (AUC={auc_n})", COLOR_NOAUG),
        (6, 7, f"{LABEL_AUG} (AUC={auc_a})",   COLOR_AUG),
    ]:
        s = Series(
            Reference(ws, min_col=y_col, min_row=2, max_row=last),
            Reference(ws, min_col=x_col, min_row=2, max_row=last),
            title=label,
        )
        s.graphicalProperties.line.solidFill = color
        s.graphicalProperties.line.width     = 18000
        ch_roc.series.append(s)

    ch_roc.width = 18; ch_roc.height = 16
    ws.add_chart(ch_roc, "K2")

    # ── Gráfica FAR/FRR vs umbral ────────────────────────────────────────
    ch_det = ScatterChart()
    ch_det.scatterStyle = "lineMarker"   # une los puntos con línea
    ch_det.title  = f"FAR / FRR vs Umbral  (EER noaug={eer_n}  |  EER aug={eer_a})"
    ch_det.style  = 10
    ch_det.x_axis.title = "Umbral de similitud"
    ch_det.y_axis.title = "Tasa de error"
    ch_det.x_axis.scaling.min = 0; ch_det.x_axis.scaling.max = 1
    ch_det.y_axis.scaling.min = 0

    thresh_ref = Reference(ws, min_col=1, min_row=2, max_row=last)
    for col_idx, label, color in [
        (4, f"FAR {LABEL_NOAUG}", COLOR_NOAUG),
        (5, f"FRR {LABEL_NOAUG}", "9DC3E6"),
        (8, f"FAR {LABEL_AUG}",   COLOR_AUG),
        (9, f"FRR {LABEL_AUG}",   "F4B183"),
    ]:
        s = Series(Reference(ws, min_col=col_idx, min_row=2, max_row=last),
                   thresh_ref, title=label)
        s.graphicalProperties.line.solidFill = color
        s.graphicalProperties.line.width     = 15000
        ch_det.series.append(s)

    ch_det.width = 18; ch_det.height = 16
    ws.add_chart(ch_det, "K26")

    # ── Tabla AUC / EER ──────────────────────────────────────────────────
    sr = last + 3
    ws.cell(row=sr,     column=1, value="Resumen").font = Font(bold=True)
    _header_row(ws, sr + 1, ["", LABEL_NOAUG, LABEL_AUG])
    for j, (lbl, vn, va) in enumerate([("AUC", auc_n, auc_a), ("EER", eer_n, eer_a)], start=2):
        ws.cell(row=sr + j, column=1, value=lbl)
        ws.cell(row=sr + j, column=2, value=vn)
        ws.cell(row=sr + j, column=3, value=va)


# ── Entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera Excel comparativo de sesiones noaug vs aug."
    )
    parser.add_argument(
        "--noaug", required=True, type=Path,
        help="CSV de la sesión sin augmentación",
    )
    parser.add_argument(
        "--aug", required=True, type=Path,
        help="CSV de la sesión con augmentación",
    )
    parser.add_argument(
        "--output", default="comparacion_sesiones.xlsx", type=Path,
        help="Ruta del Excel de salida (default: comparacion_sesiones.xlsx)",
    )
    args = parser.parse_args()

    print(f"Cargando {args.noaug} ...")
    noaug_rows = load_csv(args.noaug, "sin_aug", ANNOTATIONS_NOAUG)
    print(f"  → {len(noaug_rows)} eventos")

    print(f"Cargando {args.aug} ...")
    aug_rows = load_csv(args.aug, "con_aug", ANNOTATIONS_AUG)
    print(f"  → {len(aug_rows)} eventos")

    print("Generando Excel ...")
    wb = Workbook()
    sheet_raw_data(wb, noaug_rows + aug_rows)
    sheet_global_summary(wb, noaug_rows, aug_rows)
    sheet_per_person(wb, noaug_rows, aug_rows)
    sheet_distribution(wb, noaug_rows, aug_rows)
    sheet_classification(wb, noaug_rows, aug_rows)
    sheet_roc(wb, noaug_rows, aug_rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    print(f"Excel guardado: {args.output}")


if __name__ == "__main__":
    main()
