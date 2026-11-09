"""Small reportlab toolkit: consistent, text-selectable PDFs (NotebookLM reads the text layer)."""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle)

NAVY, TEAL, GOLD, LIGHT, GREY = colors.HexColor("#142B4D"), colors.HexColor("#1F8A8A"), colors.HexColor("#E0A12B"), colors.HexColor("#EEF2F6"), colors.HexColor("#6B7685")
GREEN, AMBER, RED = colors.HexColor("#2E7D32"), colors.HexColor("#B26A00"), colors.HexColor("#B3261E")

_MAP = {"→": "->", "←": "<-", "≥": ">=", "≤": "<=", "α": "alpha", "·": "-", "–": "-", "—": "-", "‑": "-", "✓": "[x]", "…": "...", "≈": "~", "×": "x",
        "“": '"', "”": '"', "‘": "'", "’": "'", "•": "-", "Σ": "sum", "≠": "!=", "±": "+/-", "∈": "in", "θ": "theta", "τ": "tau", "⇒": "=>", "²": "2", "ⁿ": "n", "−": "-", "►": ">", "▶": ">"}


def clean(t) -> str:
    t = str(t)
    for k, v in _MAP.items():
        t = t.replace(k, v)
    return t.encode("latin-1", "replace").decode("latin-1")


def esc(t) -> str:
    return clean(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ss = getSampleStyleSheet()
ST = {
    "title": ParagraphStyle("t", parent=ss["Title"], fontSize=26, leading=30, textColor=NAVY, alignment=0, spaceAfter=6),
    "sub": ParagraphStyle("s", parent=ss["Normal"], fontSize=12, textColor=GREY, spaceAfter=14),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=17, leading=21, textColor=NAVY, spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=13.5, leading=17, textColor=TEAL, spaceBefore=10, spaceAfter=4),
    "h3": ParagraphStyle("h3", parent=ss["Heading3"], fontSize=11.5, leading=14, textColor=NAVY, spaceBefore=6, spaceAfter=3),
    "p": ParagraphStyle("p", parent=ss["Normal"], fontSize=10, leading=14, spaceAfter=5),
    "b": ParagraphStyle("b", parent=ss["Normal"], fontSize=10, leading=13.5, leftIndent=14, bulletIndent=3, spaceAfter=2),
    "cell": ParagraphStyle("c", parent=ss["Normal"], fontSize=8.6, leading=10.8),
    "cellh": ParagraphStyle("ch", parent=ss["Normal"], fontSize=8.8, leading=11, textColor=colors.white, fontName="Helvetica-Bold"),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7.6, leading=9.2, backColor=LIGHT, leftIndent=4, rightIndent=4, borderPadding=4, spaceAfter=6),
    "note": ParagraphStyle("n", parent=ss["Normal"], fontSize=9.5, leading=13, backColor=colors.HexColor("#FFF6E0"), borderPadding=6, spaceBefore=4, spaceAfter=8),
    "cap": ParagraphStyle("cap", parent=ss["Normal"], fontSize=8.5, textColor=GREY, spaceAfter=8),
}
STATUS_COL = {"IMPLEMENTED": GREEN, "VERIFIED": GREEN, "PARTIAL": AMBER, "PLANNED": GREY, "MISSING": RED, "NOT VERIFIED": AMBER, "PENDING": AMBER}


class Doc:
    def __init__(self, filename: str, title: str, subtitle: str, sources: list[str]):
        self.f, self.title, self.s = [], title, []
        self.path = filename
        self.s.append(Paragraph(esc(title), ST["title"]))
        self.s.append(Paragraph(esc(subtitle), ST["sub"]))
        self.note("Knowledge-pack rule: every statement below is derived from files in this project or is explicitly labelled as planned, missing or not verified. "
                  "Nothing here is an invented citation, dataset, result or feature.")
        self.sources(sources)

    def sources(self, files):
        self.h2("Source files used for this document")
        self.s.append(Paragraph(esc("; ".join(files)), ST["cell"]))
        self.s.append(Spacer(1, 6))

    def h1(self, t): self.s.append(Paragraph(esc(t), ST["h1"]))
    def h2(self, t): self.s.append(Paragraph(esc(t), ST["h2"]))
    def h3(self, t): self.s.append(Paragraph(esc(t), ST["h3"]))
    def p(self, t): self.s.append(Paragraph(esc(t), ST["p"]))
    def rich(self, markup): self.s.append(Paragraph(clean(markup), ST["p"]))
    def note(self, t): self.s.append(Paragraph(esc(t), ST["note"]))
    def space(self, h=6): self.s.append(Spacer(1, h))
    def pagebreak(self): self.s.append(PageBreak())

    def bullets(self, items):
        for it in items:
            self.s.append(Paragraph(esc(it), ST["b"], bulletText="-"))
        self.s.append(Spacer(1, 4))

    def code(self, text, maxlines=60):
        lines = clean(text).splitlines()[:maxlines]
        self.s.append(Preformatted("\n".join(l[:110] for l in lines), ST["code"]))

    def table(self, header, rows, widths=None, status_col=None):
        W = A4[0] - 4 * cm
        widths = widths or [W / len(header)] * len(header)
        tot = sum(widths); widths = [w * W / tot for w in widths]
        data = [[Paragraph(esc(h), ST["cellh"]) for h in header]]
        for r in rows:
            row = []
            for j, v in enumerate(r):
                txt = esc(v)
                if status_col is not None and j == status_col and str(v).upper() in STATUS_COL:
                    txt = f'<font color="{STATUS_COL[str(v).upper()].hexval().replace("0x", "#")}"><b>{txt}</b></font>'
                row.append(Paragraph(txt, ST["cell"]))
            data.append(row)
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C7CFD8")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                               ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
        self.s.append(t); self.s.append(Spacer(1, 8))

    def image(self, path, caption, max_w=16.5 * cm, max_h=11 * cm):
        path = Path(path)
        if not path.exists():
            self.note(f"Image not available: {path.name}. ({caption})")
            return
        from PIL import Image as PI
        w, h = PI.open(path).size
        sc = min(max_w / w, max_h / h)
        self.s.append(KeepTogether([Image(str(path), w * sc, h * sc), Paragraph(esc(caption), ST["cap"])]))

    def flow(self, labels, caption, cols=4, w=3.7 * cm, h=1.3 * cm, color=TEAL):
        """Wrapped left-to-right box diagram drawn as vector graphics."""
        rows = -(-len(labels) // cols)
        gx, gy = 0.55 * cm, 0.9 * cm
        D = Drawing(cols * (w + gx), rows * (h + gy))
        for i, lab in enumerate(labels):
            r, c = divmod(i, cols)
            x, y = c * (w + gx), D.height - (r + 1) * (h + gy) + gy
            D.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=color if (i % 2 == 0) else NAVY, strokeColor=None))
            words, lines, cur = clean(lab).split(), [], ""
            for wd in words:
                if len(cur + " " + wd) > 22 and cur:
                    lines.append(cur); cur = wd
                else:
                    cur = (cur + " " + wd).strip()
            lines.append(cur)
            for k, ln in enumerate(lines[:3]):
                D.add(String(x + w / 2, y + h / 2 + (len(lines[:3]) - 1) * 4 - k * 9 - 3, ln, fontSize=7.8, fillColor=colors.white, textAnchor="middle"))
            if i < len(labels) - 1:
                if c < cols - 1:
                    x1, y1 = x + w, y + h / 2
                    D.add(Line(x1, y1, x1 + gx, y1, strokeColor=GREY, strokeWidth=1.4))
                    D.add(Polygon([x1 + gx, y1, x1 + gx - 5, y1 + 3, x1 + gx - 5, y1 - 3], fillColor=GREY, strokeColor=None))
                else:
                    x1, y1 = x + w / 2, y
                    D.add(Line(x1, y1, x1, y1 - gy + 2, strokeColor=GREY, strokeWidth=1.2, strokeDashArray=[3, 2]))
        self.s.append(KeepTogether([D, Paragraph(esc(caption), ST["cap"])]))

    def build(self, outdir: Path):
        outdir.mkdir(parents=True, exist_ok=True)
        out = outdir / self.path

        def footer(canv, doc):
            canv.saveState(); canv.setFont("Helvetica", 8); canv.setFillColor(GREY)
            canv.drawString(2 * cm, 1.1 * cm, clean(f"FinTech Cybersecurity and Consumer Trust - Research Knowledge Pack | {self.title}"))
            canv.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
            canv.setStrokeColor(TEAL); canv.setLineWidth(1.2); canv.line(2 * cm, A4[1] - 1.2 * cm, A4[0] - 2 * cm, A4[1] - 1.2 * cm)
            canv.restoreState()
        SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                          title=clean(self.title), author="FinTech Cybersecurity and Consumer Trust project").build(self.s, onFirstPage=footer, onLaterPages=footer)
        return out
