---
name: pdf
description: >
  Read, create, edit, and transform PDF files. Use when the user mentions PDF,
  .pdf, merging/splitting PDFs, extracting text or tables, OCR on scans,
  watermarking, encrypting, rendering pages, filling forms, or generating a PDF
  report. Covers pypdf, pdfplumber, reportlab, qpdf, and poppler. Do NOT use for
  native Word/Excel/PowerPoint editing (convert those formats first if needed).
---

# PDFs

## Workflow

1. Preserve the source and determine whether the PDF is born-digital, scanned, encrypted, signed, or form-based.
2. Inspect page count, dimensions, rotation, metadata, text extractability, and form fields as relevant.
3. Use the least destructive operation and write a new output file by default.
4. Reopen the output, verify expected page/content properties, then render and inspect every changed page.
5. Warn when an operation invalidates digital signatures, removes accessibility structure, or relies on OCR.

## Tool choice

| Goal | Tool |
|------|------|
| Extract text | `pdfplumber` or `pdftotext -layout` |
| Extract tables | `pdfplumber` → pandas |
| Merge / split / rotate / encrypt | `pypdf` or `qpdf` |
| Create new PDF | **reportlab** (Platypus for flow, Canvas for absolute) |
| Render pages to images | `pdftoppm` / `pdf2image` |
| Embedded images out | `pdfimages -all` |
| OCR scans | `pdf2image` + `pytesseract` |
| Fill forms | see [references/forms.md](references/forms.md) |
| Low-level repair | `qpdf` |

```bash
pip install pypdf pdfplumber reportlab pdf2image pytesseract
# system: poppler-utils, qpdf, tesseract-ocr
```

Deep dives: [references/forms.md](references/forms.md), [references/generation.md](references/generation.md)

---

## Extract

### Text

```python
import pdfplumber

with pdfplumber.open("report.pdf") as doc:
    text = "\n".join(page.extract_text() or "" for page in doc.pages)
```

```bash
pdftotext -layout report.pdf report.txt
pdftotext -f 2 -l 5 report.pdf slice.txt
```

### Tables

```python
import pdfplumber, pandas as pd

frames = []
with pdfplumber.open("report.pdf") as doc:
    for page in doc.pages:
        for table in page.extract_tables():
            if table:
                frames.append(pd.DataFrame(table[1:], columns=table[0]))
if frames:
    pd.concat(frames, ignore_index=True).to_excel("tables.xlsx", index=False)
```

### Metadata

```python
from pypdf import PdfReader
info = PdfReader("report.pdf").metadata
print(info.title, info.author)
```

### Scanned PDFs (OCR)

If `extract_text` is empty/garbage, rasterize then OCR:

```python
import pytesseract
from pdf2image import convert_from_path

pages = convert_from_path("scan.pdf", dpi=300)
text = "\n\n".join(pytesseract.image_to_string(p) for p in pages)
```

---

## Reorganize

### Merge

```python
from pypdf import PdfWriter
w = PdfWriter()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    w.append(path)
with open("merged.pdf", "wb") as f:
    w.write(f)
```

```bash
qpdf --empty --pages a.pdf b.pdf c.pdf -- merged.pdf
```

### Split

```python
from pypdf import PdfReader, PdfWriter
src = PdfReader("merged.pdf")
for i, page in enumerate(src.pages, 1):
    w = PdfWriter(); w.add_page(page)
    with open(f"page_{i:02d}.pdf", "wb") as f:
        w.write(f)
```

```bash
qpdf input.pdf --pages . 1-5 -- first5.pdf
```

### Rotate

```python
from pypdf import PdfReader, PdfWriter

src = PdfReader("sideways.pdf")
w = PdfWriter()
for p in src.pages:
    p.rotate(90)  # multiples of 90
    w.add_page(p)
with open("rotated.pdf", "wb") as f:
    w.write(f)
```

### Watermark

```python
from pypdf import PdfReader, PdfWriter

stamp = PdfReader("stamp.pdf").pages[0]
src = PdfReader("contract.pdf")
w = PdfWriter()
for p in src.pages:
    p.merge_page(stamp)
    w.add_page(p)
with open("watermarked.pdf", "wb") as f:
    w.write(f)
```

### Encrypt

```python
from pypdf import PdfWriter

w = PdfWriter()
w.append("private.pdf")
w.encrypt(user_password="open", owner_password="owner")
with open("locked.pdf", "wb") as f:
    w.write(f)
```

```bash
qpdf --password=open --decrypt locked.pdf unlocked.pdf
```

---

## Create (reportlab)

Prefer **Platypus** for multi-page documents; **Canvas** for precise single-page layouts (certificates, labels).

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether,
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="H1Custom", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=18, textColor=colors.HexColor("#0F172A"),
    spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="Body", parent=styles["Normal"],
    fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#1F2937"),
))

story = [
    Paragraph("Quarterly Report", styles["H1Custom"]),
    Spacer(1, 0.2 * inch),
    Paragraph("Narrative text flows and wraps automatically. " * 8, styles["Body"]),
]

# Tables: ALWAYS wrap cell text in Paragraph; ALWAYS set colWidths
body = styles["Body"]
rows = [
    [Paragraph("<b>Metric</b>", body), Paragraph("<b>Value</b>", body)],
    [Paragraph("Revenue", body), Paragraph("$4.2M", body)],
    [Paragraph("Notes with long prose that must wrap inside the cell.", body),
     Paragraph("OK", body)],
]
tbl = Table(rows, colWidths=[4.5 * inch, 2 * inch], repeatRows=1)
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(Spacer(1, 0.3 * inch))
story.append(tbl)

doc = SimpleDocTemplate(
    "report.pdf", pagesize=letter,
    leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
)
doc.build(story)
```

### Canvas essentials

Origin is **bottom-left**; y increases upward.

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("note.pdf", pagesize=letter)
_, h = letter
c.setFont("Helvetica-Bold", 16)
c.drawString(72, h - 72, "One inch from top-left")
c.save()
```

### Subscripts / superscripts

Do **not** use Unicode ₂ ⁹ — built-in fonts lack glyphs (black boxes). Use:

```python
Paragraph("H<sub>2</sub>O and E = mc<super>2</super>", styles["Body"])
```

### Images

Preserve aspect ratio:

```python
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image

# Platypus
img = Image("chart.png", width=5 * inch, height=2.8 * inch, hAlign="CENTER")

# Canvas
ir = ImageReader("chart.png")
iw, ih = ir.getSize()
w = 5 * inch
h = w * ih / iw
c.drawImage(ir, inch, page_h - inch - h, width=w, height=h)
```

---

## Visual QA (always)

After generating or filling a PDF, render and inspect:

```bash
pdftoppm -png -r 150 output.pdf /tmp/pdfpage
# opens /tmp/pdfpage-1.png, /tmp/pdfpage-2.png, ...
```

Check: margins, overflow, overlapping elements, table clipping, form values beside wrong labels, low contrast.

---

## Forms

Filling AcroForm fields or stamping text onto flat PDFs: follow [references/forms.md](references/forms.md).

---

## Dependencies

```bash
pip install pypdf pdfplumber reportlab pdf2image pytesseract Pillow
# Debian/Ubuntu: sudo apt install poppler-utils qpdf tesseract-ocr
```
