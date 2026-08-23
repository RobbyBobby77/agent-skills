# PDF Generation Details (reportlab)

## Page sizes

```python
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch, mm

pagesize = letter                 # 612 × 792 pt
pagesize = A4
pagesize = landscape(letter)      # wide tables
```

## Custom styles

```python
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle",
    fontName="Helvetica-Bold",
    fontSize=28,
    leading=34,
    textColor=colors.HexColor("#0F172A"),
    alignment=TA_CENTER,
    spaceAfter=20,
))
styles.add(ParagraphStyle(
    name="SmallMuted",
    fontName="Helvetica",
    fontSize=8,
    textColor=colors.HexColor("#64748B"),
))
```

Inline markup in Paragraphs: `<b>`, `<i>`, `<u>`, `<br/>`, `<font color="red">`, `<a href="url">`, `<super>`, `<sub>`.

Escape user content: `&` → `&amp;`, `<` → `&lt;`.

## Headers / footers / page numbers

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.4, 0.45, 0.5)
    canvas.drawString(inch, 0.5 * inch, "Confidential")
    canvas.drawRightString(doc.pagesize[0] - inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate("out.pdf", pagesize=letter,
                        leftMargin=inch, rightMargin=inch,
                        topMargin=inch, bottomMargin=0.75 * inch)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
```

## Multi-column-ish layouts

Use nested tables for side-by-side content (Platypus has no real CSS grid):

```python
from reportlab.platypus import KeepInFrame, Table

left = [Paragraph("<b>Left</b>", styles["Body"]), Paragraph("...", styles["Body"])]
right = [Paragraph("<b>Right</b>", styles["Body"]), Paragraph("...", styles["Body"])]
left_frame = KeepInFrame(3.25 * inch, 4 * inch, left)
right_frame = KeepInFrame(3.25 * inch, 4 * inch, right)
pair = Table([[left_frame, right_frame]], colWidths=[3.25 * inch, 3.25 * inch])
```

## Page breaks & keep-together

```python
from reportlab.platypus import PageBreak, KeepTogether, CondPageBreak

story.append(PageBreak())
story.append(KeepTogether([heading, para, table]))  # avoid orphan headers
story.append(CondPageBreak(2 * inch))  # break if less than 2" left
```

## Long tables

```python
tbl = Table(rows, colWidths=[...], repeatRows=1)  # header repeats each page
```

If too wide: `landscape(letter)` or split columns across pages — don't shrink fonts below ~8pt.

## Fonts

Built-ins: Helvetica, Times-Roman, Courier (+ Bold/Oblique).

Custom TTF:

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("Inter", "/path/to/Inter-Regular.ttf"))
```

## Performance

- Prefer `drawImage` over `drawInlineImage` for repeated logos
- Downscale huge PNGs before embedding
- For 100+ page data dumps, consider generating CSV/XLSX instead of PDF
