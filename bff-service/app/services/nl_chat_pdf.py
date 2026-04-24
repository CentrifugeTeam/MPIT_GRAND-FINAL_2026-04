"""Сборка PDF из одного ответа ассистента NL-чата (по message_id)."""

from __future__ import annotations

import io
import os
import re
import unicodedata
from typing import Any
from urllib.parse import quote

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MAX_TABLE_ROWS = 90
MAX_LABELS_CHART = 120
_FILENAME_BAD = '<>:"/\\|?*\n\r\t'

# Helvetica не рисует кириллицу → «чёрные квадраты». Ищем DejaVu (есть в Docker-образе bff).
_DEJAVU_REG_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/opt/homebrew/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/local/share/fonts/truetype/DejaVuSans.ttf",
)
_DEJAVU_BOLD_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/opt/homebrew/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/local/share/fonts/truetype/DejaVuSans-Bold.ttf",
)

_PDF_FONT_REG = "Helvetica"
_PDF_FONT_BOLD = "Helvetica-Bold"
_MATPLOTLIB_CYRILLIC_READY = False
_PDF_FONT_INIT_DONE = False


def _first_existing(paths: tuple[str, ...]) -> str | None:
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def _ensure_unicode_pdf_fonts() -> tuple[str, str]:
    """Регистрирует TTF один раз; возвращает (regular, bold) имена для reportlab."""
    global _PDF_FONT_REG, _PDF_FONT_BOLD, _PDF_FONT_INIT_DONE
    if _PDF_FONT_INIT_DONE:
        return _PDF_FONT_REG, _PDF_FONT_BOLD
    _PDF_FONT_INIT_DONE = True
    reg_path = _first_existing(_DEJAVU_REG_CANDIDATES)
    if not reg_path:
        return _PDF_FONT_REG, _PDF_FONT_BOLD
    bold_path = _first_existing(_DEJAVU_BOLD_CANDIDATES) or reg_path
    try:
        pdfmetrics.registerFont(TTFont("NlPdfSans", reg_path))
        pdfmetrics.registerFont(TTFont("NlPdfSans-Bold", bold_path))
        _PDF_FONT_REG = "NlPdfSans"
        _PDF_FONT_BOLD = "NlPdfSans-Bold"
    except Exception:
        _PDF_FONT_REG = "Helvetica"
        _PDF_FONT_BOLD = "Helvetica-Bold"
    return _PDF_FONT_REG, _PDF_FONT_BOLD


def _ensure_matplotlib_cyrillic() -> None:
    """Подписи на графиках с кириллицей (ось X и легенда)."""
    global _MATPLOTLIB_CYRILLIC_READY
    if _MATPLOTLIB_CYRILLIC_READY:
        return
    reg_path = _first_existing(_DEJAVU_REG_CANDIDATES)
    if reg_path:
        try:
            font_manager.fontManager.addfont(reg_path)
            prop = font_manager.FontProperties(fname=reg_path)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
        except Exception:
            pass
    _MATPLOTLIB_CYRILLIC_READY = True


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cell_text(v: Any, max_len: int = 80) -> str:
    if v is None:
        return ""
    t = str(v)
    if len(t) > max_len:
        return t[: max_len - 1] + "…"
    return t


def _sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(row: dict[str, Any]) -> str:
        ca = row.get("created_at")
        if ca is None:
            return ""
        if isinstance(ca, str):
            return ca
        if hasattr(ca, "isoformat"):
            return ca.isoformat()  # type: ignore[no-any-return]
        return str(ca)

    return sorted((i for i in items if isinstance(i, dict)), key=sort_key)


def _assistant_text_block_no_reasoning(payload: dict[str, Any]) -> str:
    """Текст ответа без reasoning (цепочка мыслей не попадает в PDF)."""
    parts: list[str] = []
    text = str(payload.get("text") or "").strip()
    report = payload.get("report")
    if report is not None and str(report).strip():
        parts.append(str(report).strip())
    elif text:
        parts.append(text)
    err = payload.get("error")
    if err is not None and str(err).strip():
        parts.append(f"Ошибка: {str(err).strip()}")
    status = payload.get("status")
    st = str(status or "").strip().lower()
    if st and st not in ("done", "complete", "ok", ""):
        parts.append(f"Статус: {status}")
    sql = payload.get("sql")
    if sql is not None and str(sql).strip():
        parts.append(f"SQL:\n{str(sql).strip()}")
    if not parts and text:
        parts.append(text)
    return "\n\n".join(parts)


def _float_or_nan(v: Any) -> float:
    if v is None or v == "":
        return float("nan")
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def chart_to_png_bytes(chart_payload: dict[str, Any]) -> bytes | None:
    _ensure_matplotlib_cyrillic()
    ctype = str(chart_payload.get("type") or "").lower()
    if ctype not in ("bar", "line"):
        return None
    labels = chart_payload.get("labels") or []
    series_raw = chart_payload.get("series") or []
    if not isinstance(labels, list) or not labels:
        return None
    series_list = [s for s in series_raw if isinstance(s, dict)]
    if not series_list:
        return None

    n = min(len(labels), MAX_LABELS_CHART)
    x = list(range(n))
    label_strs = [_cell_text(labels[i], 20) for i in range(n)]

    rc = {
        "text.color": "#222222",
        "axes.labelcolor": "#222222",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "legend.labelcolor": "#222222",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
    with plt.rc_context(rc):
        fig = plt.figure(figsize=(8, 3.8), dpi=120, facecolor="white")
        ax = fig.add_subplot(111, facecolor="white")
        ax.tick_params(colors="#333333")
        for spine in ax.spines.values():
            spine.set_color("#cccccc")

        if ctype == "bar" and len(series_list) == 1:
            ser = series_list[0]
            raw = list(ser.get("data") or [])[:n]
            ys = [_float_or_nan(raw[i] if i < len(raw) else None) for i in range(n)]
            ax.bar(x, ys, width=0.65, color="#4472c4", alpha=0.9)
        else:
            for ser in series_list:
                name = str(ser.get("label") or ser.get("key") or "series")
                raw = list(ser.get("data") or [])
                ys = [_float_or_nan(raw[i] if i < len(raw) else None) for i in range(n)]
                if ctype == "line" or len(series_list) > 1:
                    ax.plot(x, ys, marker="o", markersize=2.5, label=name, linewidth=1.3)
                else:
                    ax.bar(x, ys, width=0.5, alpha=0.75, label=name)
            if len(series_list) > 1 or ctype == "line":
                ax.legend(fontsize=7, loc="best", framealpha=0.95, facecolor="white")

        ax.set_xticks(x)
        ax.set_xticklabels(label_strs, rotation=38, ha="right", fontsize=7, color="#333333")
        ax.grid(True, alpha=0.28, color="#bbbbbb")
        ax.set_facecolor("white")
        fig.subplots_adjust(bottom=0.22, left=0.08, right=0.98, top=0.92)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.12, facecolor="white")
        plt.close(fig)
    buf.seek(0)
    return buf.read()


def _table_flowable(
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    font_reg: str,
    font_bold: str,
) -> tuple[Table, int]:
    header = [_cell_text(c, 36) for c in columns]
    data: list[list[str]] = [header]
    shown = min(len(rows), MAX_TABLE_ROWS)
    for i in range(shown):
        r = rows[i] if isinstance(rows[i], dict) else {}
        data.append([_cell_text(r.get(c), 56) for c in columns])
    omitted = max(0, len(rows) - shown)
    tw = Table(data, repeatRows=1)
    text_color = colors.HexColor("#222222")
    tw.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                ("FONTNAME", (0, 0), (-1, -1), font_reg),
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("TEXTCOLOR", (0, 0), (-1, -1), text_color),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("GRID", (0, 0), (-1, -1), 0.2, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f8f8")]),
            ]
        )
    )
    return tw, omitted


def _clean_question_for_filename(q: str) -> str:
    s = (q or "").strip()[:150]
    for c in _FILENAME_BAD:
        s = s.replace(c, " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80] if s else ""


def pdf_download_filenames(question: str, message_id: str) -> tuple[str, str]:
    """
    (ascii для filename=, полное имя с расширением .pdf для filename*=UTF-8'').
    """
    base = _clean_question_for_filename(question)
    if not base:
        short_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", message_id.strip())[:16] or "answer"
        return f"answer-{short_id}.pdf", f"answer-{short_id}.pdf"
    stem = base[:-4] if base.lower().endswith(".pdf") else base
    utf_name = f"{stem}.pdf"
    # ASCII fallback: латиница + цифры из NFKD, иначе короткий id
    ascii_try = "".join(
        c
        for c in unicodedata.normalize("NFKD", stem)
        if unicodedata.category(c) != "Mn" and c.isascii() and (c.isalnum() or c in " ._-")
    )
    ascii_try = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_try).strip("-_.") or ""
    if len(ascii_try) < 2:
        short_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", message_id.strip())[:12] or "x"
        ascii_name = f"answer-{short_id}.pdf"
    else:
        ascii_stem = ascii_try[:50].rstrip("-.")
        ascii_name = f"{ascii_stem}.pdf"
    return ascii_name, utf_name


def content_disposition_attachment(ascii_filename: str, utf8_filename: str) -> str:
    enc = quote(utf8_filename, safe="")
    # RFC 5987: filename*=UTF-8''encoded
    return f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{enc}"


def find_assistant_payload_and_question(
    transcript: dict[str, Any], message_id: str
) -> tuple[dict[str, Any], str]:
    items_in = transcript.get("items") or []
    items = _sort_items([i for i in items_in if isinstance(i, dict)])
    idx: int | None = None
    for i, it in enumerate(items):
        if str(it.get("id") or "") == message_id:
            idx = i
            break
    if idx is None:
        raise KeyError("message_not_found")
    if str(items[idx].get("role") or "").lower() != "assistant":
        raise ValueError("Укажите message_id сообщения ассистента")
    question = ""
    for j in range(idx - 1, -1, -1):
        if str(items[j].get("role") or "").lower() == "user":
            pl = items[j].get("payload") if isinstance(items[j].get("payload"), dict) else {}
            question = str(pl.get("text") or "").strip()
            break
    payload = items[idx].get("payload") if isinstance(items[idx].get("payload"), dict) else {}
    return payload, question


def build_single_assistant_message_pdf_bytes(
    transcript: dict[str, Any],
    message_id: str,
) -> tuple[bytes, str]:
    """
    PDF только для одного ответа ассистента + заголовок с вопросом пользователя.
    Возвращает (bytes, Content-Disposition значение без префикса attachment если нужно — здесь полная строка).
    """
    payload, question = find_assistant_payload_and_question(transcript, message_id)
    ascii_fn, utf_fn = pdf_download_filenames(question, message_id)
    disposition = content_disposition_attachment(ascii_fn, utf_fn)

    font_reg, font_bold = _ensure_unicode_pdf_fonts()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    page_w = doc.width
    styles = getSampleStyleSheet()
    q_style = ParagraphStyle(
        name="PdfQuestion",
        parent=styles["Heading2"],
        fontName=font_bold,
        fontSize=11,
        textColor=colors.HexColor("#222222"),
        spaceAfter=8,
        leading=14,
    )
    body_style = ParagraphStyle(
        name="PdfBody",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#222222"),
    )
    story: list[Any] = []

    if question:
        story.append(Paragraph(_xml_escape(question).replace("\n", "<br/>"), q_style))
    else:
        story.append(Paragraph(_xml_escape("Ответ"), q_style))

    block = _assistant_text_block_no_reasoning(payload)
    if block:
        story.append(Paragraph(_xml_escape(block).replace("\n", "<br/>"), body_style))

    cp = payload.get("chart_payload")
    png_data: bytes | None = None
    if isinstance(cp, dict) and cp:
        png_data = chart_to_png_bytes(cp)
        if png_data:
            story.append(Spacer(1, 0.1 * cm))
            story.append(Image(io.BytesIO(png_data), width=page_w))

    cols_raw = payload.get("columns")
    rows_raw = payload.get("rows")
    has_table = (
        isinstance(cols_raw, list)
        and cols_raw
        and isinstance(rows_raw, list)
        and rows_raw
    )
    if has_table:
        columns = [str(c) for c in cols_raw]
        row_dicts = [dict(r) if isinstance(r, dict) else {} for r in rows_raw]
        tbl, omitted = _table_flowable(columns, row_dicts, font_reg=font_reg, font_bold=font_bold)
        story.append(Spacer(1, 0.1 * cm))
        story.append(tbl)
        if omitted:
            story.append(Spacer(1, 0.06 * cm))
            story.append(
                Paragraph(
                    _xml_escape(f"… не показано строк в таблице: {omitted}."),
                    body_style,
                )
            )

    has_chart = png_data is not None
    if not block and not has_chart and not has_table:
        story.append(
            Paragraph(
                _xml_escape("(В сообщении нет текста, графика и таблицы.)"),
                body_style,
            ),
        )

    doc.build(story)
    buf.seek(0)
    return buf.getvalue(), disposition
