# PDF Form Filling

## 1. Detect form type

```python
from pypdf import PdfReader

reader = PdfReader("form.pdf")
fields = reader.get_fields()  # None / {} → not a fillable AcroForm
if fields:
    for name, meta in fields.items():
        print(name, meta.get("/FT"), meta.get("/V"))
```

```bash
# CLI survey
python -c "from pypdf import PdfReader; print(PdfReader('form.pdf').get_fields())"
pdftotext -layout form.pdf - | head  # understand labels visually
pdftoppm -png -r 120 form.pdf /tmp/form  # SEE the form
```

## 2. Fillable AcroForm

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("form.pdf")
writer = PdfWriter()
writer.append(reader)

# Field names are NOT the visible labels — use get_fields() keys
writer.update_page_form_field_values(
    writer.pages[0],
    {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "agree": "/Yes",   # checkboxes often /Yes or /On
    },
)

# Need appearances flattened for universal viewers?
# writer.set_need_appearances_writer(True)  # if available in version
with open("filled.pdf", "wb") as f:
    writer.write(f)
```

Tips:
- Always map **field names → values**, never guess from label text alone
- Checkboxes/radio values are often export values like `/Yes`, `/On`, `/1` — inspect the field dict
- Re-render pages after fill; wrong field mapping is the #1 bug
- Some forms need `needAppearances` for text to show in every viewer

## 3. Flat / scanned form (no fields)

Overlay text with reportlab + merge, or use annotation approach.

```python
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=letter)
c.setFont("Helvetica", 10)
# coordinates: bottom-left origin — measure from rendered page image
c.drawString(72, 700, "Ada Lovelace")
c.drawString(72, 680, "1832-12-10")
c.save()
packet.seek(0)

overlay = PdfReader(packet)
base = PdfReader("flat_form.pdf")
writer = PdfWriter()
page = base.pages[0]
page.merge_page(overlay.pages[0])
writer.add_page(page)
# copy remaining pages...
with open("filled_flat.pdf", "wb") as f:
    writer.write(f)
```

### Measuring coordinates

1. `pdftoppm -png -r 150 form.pdf /tmp/f`
2. Open the PNG; note x,y in pixels from **top-left**
3. Convert to PDF points (72 pt/inch):

```
pt_x = px_x * 72 / dpi
pt_y = page_height_pt - (px_y * 72 / dpi)  # flip Y
```

US Letter page height ≈ 792 pt.

## 4. QA loop

1. Fill
2. `pdftoppm` every page
3. Confirm each value sits on the correct line, nothing clipped, checkboxes ticked
4. Fix coordinates/field map
5. Repeat

Never trust field dumps alone — **visual check is mandatory**.
