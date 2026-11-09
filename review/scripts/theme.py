"""Shared theme + helpers for the four review decks. Everything is native PowerPoint (editable shapes, tables, charts)."""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review"
NAVY, TEAL, GOLD = RGBColor(0x14, 0x2B, 0x4D), RGBColor(0x1F, 0x8A, 0x8A), RGBColor(0xE0, 0xA1, 0x2B)
INK, MUTED, LIGHT, WHITE = RGBColor(0x22, 0x2B, 0x38), RGBColor(0x6B, 0x76, 0x85), RGBColor(0xEE, 0xF2, 0xF6), RGBColor(255, 255, 255)
RED = RGBColor(0xC1, 0x12, 0x1F)
FONT = "Calibri"
TITLE = "FinTech Cybersecurity and Consumer Trust"
PLACEHOLDER = "[Student name] · [Register no.] · Guide: [Guide name] · [Department / Institution]"


def new_deck() -> Presentation:
    p = Presentation()
    p.slide_width, p.slide_height = Inches(13.333), Inches(7.5)
    return p


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _text(shape_or_tf, text, size=18, bold=False, color=INK, align=None, font=FONT):
    tf = shape_or_tf.text_frame if hasattr(shape_or_tf, "text_frame") else shape_or_tf
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = ""
    r = p.add_run(); r.text = text
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, font
    if align:
        p.alignment = align
    return p


def box(slide, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, text="", size=14, bold=False, color=INK, align=PP_ALIGN.CENTER):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line; s.line.width = Pt(1.25)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    tf = s.text_frame; tf.margin_left = tf.margin_right = Inches(0.08); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    if text:
        _text(s, text, size, bold, color, align)
    return s


def arrow(slide, x1, y1, x2, y2, color=MUTED):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb, c.line.width = color, Pt(2)
    ln = c.line._get_or_add_ln()
    from lxml import etree
    ln.append(etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", type="triangle"))
    return c


def _chrome(slide, title, review_no, n):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.0))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    acc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.0), Inches(13.333), Inches(0.06))
    acc.fill.solid(); acc.fill.fore_color.rgb = TEAL; acc.line.fill.background()
    t = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(12.3), Inches(0.7))
    _text(t, title, 28, True, WHITE)
    f = slide.shapes.add_textbox(Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.35))
    _text(f, f"{TITLE}  |  Review {review_no}  |  {n}", 10, False, MUTED)


class Deck:
    def __init__(self, review_no: int, subtitle: str):
        self.prs, self.no, self.n = new_deck(), review_no, 0
        self._title_slide(subtitle)

    def _title_slide(self, subtitle):
        s = _blank(self.prs)
        bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
        band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(3.55), Inches(13.333), Inches(0.08))
        band.fill.solid(); band.fill.fore_color.rgb = GOLD; band.line.fill.background()
        t = s.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(11.5), Inches(1.2)); _text(t, TITLE, 40, True, WHITE)
        t = s.shapes.add_textbox(Inches(0.8), Inches(2.4), Inches(11.5), Inches(1)); _text(t, f"Monthly Project Review {self.no} - {subtitle}", 24, False, RGBColor(0xBF, 0xD7, 0xEA))
        t = s.shapes.add_textbox(Inches(0.8), Inches(4.0), Inches(11.5), Inches(1.2)); _text(t, "Final-year research & development project", 18, False, WHITE)
        t = s.shapes.add_textbox(Inches(0.8), Inches(4.7), Inches(11.5), Inches(1.0)); _text(t, PLACEHOLDER, 14, False, RGBColor(0xBF, 0xD7, 0xEA))
        t = s.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(11.5), Inches(0.5)); _text(t, "Edit the bracketed placeholders on this slide before presenting.", 11, False, GOLD)

    def slide(self, title):
        s = _blank(self.prs); self.n += 1
        _chrome(s, title, self.no, self.n)
        return s

    def bullets(self, title, items, note=None, size=20):
        s = self.slide(title)
        tb = s.shapes.add_textbox(Inches(0.6), Inches(1.35), Inches(12.1), Inches(5.2)); tf = tb.text_frame; tf.word_wrap = True
        first = True
        for it in items:
            lvl = 1 if isinstance(it, tuple) else 0
            txt = it[0] if isinstance(it, tuple) else it
            p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
            p.text = ""; r = p.add_run(); r.text = ("•  " if lvl == 0 else "–  ") + txt
            r.font.size, r.font.name = Pt(size if lvl == 0 else size - 3), FONT
            r.font.color.rgb = INK if lvl == 0 else MUTED
            p.level = lvl; p.space_after = Pt(8)
        if note:
            box(s, 0.6, 6.25, 12.1, 0.65, LIGHT, TEAL, text=note, size=13, color=NAVY)
        return s

    def table(self, title, header, rows, widths=None, note=None, size=13):
        s = self.slide(title)
        h = min(0.42 * (len(rows) + 1), 5.0)
        gt = s.shapes.add_table(len(rows) + 1, len(header), Inches(0.6), Inches(1.4), Inches(12.1), Inches(h)).table
        for j, hd in enumerate(header):
            c = gt.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = NAVY; _text(c, str(hd), size, True, WHITE)
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row):
                c = gt.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = LIGHT if i % 2 else WHITE
                _text(c, str(v), size, False, INK)
        if widths:
            for j, w in enumerate(widths):
                gt.columns[j].width = Inches(w)
        if note:
            box(s, 0.6, 6.3, 12.1, 0.6, LIGHT, TEAL, text=note, size=12, color=NAVY)
        return s

    def flow(self, title, steps, note=None, cols=None, colors=None):
        """Left-to-right (wrapping) process diagram built from native shapes + connectors."""
        s = self.slide(title)
        cols = cols or min(len(steps), 5)
        w, h, gx, gy = 2.1, 1.1, 0.45, 0.9
        rows_n = -(-len(steps) // cols)
        x0 = (13.333 - (cols * w + (cols - 1) * gx)) / 2
        for i, st in enumerate(steps):
            r, c = divmod(i, cols)
            x, y = x0 + c * (w + gx), 1.6 + r * (h + gy)
            box(s, x, y, w, h, (colors or {}).get(i, TEAL if i % 2 == 0 else NAVY), text=st, size=13, bold=True, color=WHITE)
            if i < len(steps) - 1:
                if c < cols - 1:
                    arrow(s, x + w, y + h / 2, x + w + gx, y + h / 2)
                else:
                    arrow(s, x + w / 2, y + h, x0 + w / 2, y + h + gy)
        if note:
            box(s, 0.6, 6.2, 12.1, 0.7, LIGHT, TEAL, text=note, size=13, color=NAVY)
        return s

    def image(self, title, path, caption, max_w=12.0, max_h=4.9):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"{path} missing - run the pipeline first (no placeholder figures are fabricated)")
        s = self.slide(title)
        from PIL import Image
        w, h = Image.open(path).size
        sc = min(max_w / w, max_h / h) * 1.0
        pw, ph = w * sc, h * sc
        s.shapes.add_picture(str(path), Inches((13.333 - pw) / 2), Inches(1.3), Inches(pw), Inches(ph))
        t = s.shapes.add_textbox(Inches(0.6), Inches(6.4), Inches(12.1), Inches(0.6)); _text(t, caption, 12, False, MUTED)
        return s

    def bar_chart(self, title, cats, series: dict, caption, number_format='0.000', horizontal=False):
        s = self.slide(title)
        cd = CategoryChartData(); cd.categories = cats
        for k, v in series.items():
            cd.add_series(k, v)
        kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
        ch = s.shapes.add_chart(kind, Inches(0.7), Inches(1.3), Inches(11.9), Inches(4.8), cd).chart
        ch.has_legend = len(series) > 1
        if ch.has_legend:
            ch.legend.position, ch.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
        pl = ch.plots[0]; pl.has_data_labels = True
        pl.data_labels.number_format, pl.data_labels.number_format_is_linked = number_format, False
        pl.data_labels.font.size = Pt(10)
        palette = [TEAL, NAVY, GOLD, RED, MUTED, RGBColor(0x7B, 0x2C, 0xBF)]
        for i, se in enumerate(pl.series):
            se.format.fill.solid(); se.format.fill.fore_color.rgb = palette[i % len(palette)]
        t = s.shapes.add_textbox(Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.6)); _text(t, caption, 12, False, MUTED)
        return s

    def two_col(self, title, left_title, left, right_title, right):
        s = self.slide(title)
        for x, ttl, items in ((0.6, left_title, left), (6.9, right_title, right)):
            box(s, x, 1.35, 5.8, 0.55, TEAL, text=ttl, size=16, bold=True, color=WHITE)
            tb = s.shapes.add_textbox(Inches(x), Inches(2.0), Inches(5.8), Inches(4.7)); tf = tb.text_frame; tf.word_wrap = True
            for i, it in enumerate(items):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.text = ""
                r = p.add_run(); r.text = "•  " + it; r.font.size, r.font.name, r.font.color.rgb = Pt(16), FONT, INK; p.space_after = Pt(6)
        return s

    def save(self, name):
        p = OUT / name; self.prs.save(p); print("wrote", p.relative_to(ROOT), f"({self.n + 1} slides)")


def load_summary() -> dict:
    p = ROOT / "models" / "model_metadata" / "last_run_summary.json"
    if not p.exists():
        raise FileNotFoundError("Run the pipeline first: results slides use only real run output (no fabricated numbers).")
    return json.loads(p.read_text())


def architecture(deck: Deck, title="System architecture (Docker Compose)"):
    s = deck.slide(title)
    box(s, 0.5, 1.35, 12.3, 5.4, WHITE, MUTED, shape=MSO_SHAPE.RECTANGLE)
    t = s.shapes.add_textbox(Inches(0.6), Inches(1.38), Inches(6), Inches(0.35)); _text(t, "Docker network: fintech-net (ports bound to localhost)", 11, False, MUTED)
    box(s, 0.9, 2.0, 2.4, 1.0, NAVY, text="Worker\nPython pipeline\n+ /metrics :8000", size=12, bold=True, color=WHITE)
    box(s, 0.9, 4.1, 2.4, 1.0, NAVY, text="JupyterLab\n:8888", size=12, bold=True, color=WHITE)
    box(s, 4.2, 2.0, 2.3, 1.0, TEAL, text="PostgreSQL\nresults + metadata", size=12, bold=True, color=WHITE)
    box(s, 4.2, 4.1, 2.3, 1.0, TEAL, text="Promtail →\nLoki (logs)", size=12, bold=True, color=WHITE)
    box(s, 7.4, 2.0, 2.2, 1.0, GOLD, text="Prometheus\n:9090", size=12, bold=True, color=INK)
    box(s, 7.4, 4.1, 2.2, 1.0, GOLD, text="cAdvisor\ncontainer stats", size=12, bold=True, color=INK)
    box(s, 10.4, 3.05, 2.2, 1.1, RED, text="Grafana :3000\n7 dashboards\nalerts", size=12, bold=True, color=WHITE)
    arrow(s, 3.3, 2.5, 4.2, 2.5); arrow(s, 3.3, 2.7, 7.4, 2.7); arrow(s, 3.3, 4.4, 4.2, 4.4)
    arrow(s, 9.6, 2.5, 10.4, 3.4); arrow(s, 6.5, 4.6, 10.4, 3.9); arrow(s, 6.5, 2.4, 10.4, 3.2); arrow(s, 8.5, 4.1, 8.5, 3.0)
    t = s.shapes.add_textbox(Inches(0.6), Inches(5.5), Inches(12), Inches(1.2))
    _text(t, "Worker writes results to PostgreSQL and JSON logs (→ Promtail → Loki); Prometheus scrapes worker, cAdvisor, Loki and Grafana; "
             "Grafana queries Prometheus (PromQL), Loki (LogQL) and PostgreSQL (SQL). Jupyter reads the artefacts the worker produced.", 13, False, INK)
    return s
