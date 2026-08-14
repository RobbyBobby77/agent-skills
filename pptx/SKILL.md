---
name: pptx
description: >
  Create, read, edit, and QA PowerPoint presentations (.pptx). Use for any slide
  deck, pitch deck, presentation, keynote-style deliverable, or when a .pptx file
  is input or output. Covers PptxGenJS creation, reading with markitdown/python-pptx,
  design systems, charts, icons, and mandatory visual QA. Do NOT use for Word,
  Excel, or PDF-only tasks.
---

# PowerPoint (PPTX)

## Related skills

| Need | Skill |
|------|-------|
| Architecture figures to embed | `diagrams` |
| Charts from data | `data-analysis` |
| Word / Excel / PDF | `docx` / `xlsx` / `pdf` |

## Workflow

1. Preserve the source and inspect slide size, masters, layouts, theme, fonts, notes, and existing visual language.
2. Outline the narrative before laying out slides; give each slide one job and a clear takeaway.
3. Edit existing decks with the smallest tool that preserves their structure; do not rebuild branded templates.
4. Generate, extract content for QA, render every slide, and complete at least one fix-and-render cycle.
5. Deliver a new file and report any fonts, linked media, animations, or features that were not preserved.

## Workflow selection

| Situation | Action |
|-----------|--------|
| Existing `.pptx` attached | Edit it (python-pptx or unpack XML) — don't rebuild |
| Create from scratch | **PptxGenJS** (preferred) — see below + [references/creating.md](references/creating.md) |
| Read / summarize | `python -m markitdown file.pptx` |

---

## Create from scratch (PptxGenJS)

```bash
npm install pptxgenjs
# optional icons:
npm install react react-dom react-icons sharp
```

```javascript
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" × 5.625"
pres.author = "Agent";
pres.title = "Q3 Strategy";

const C = {
  bg: "0F172A",
  card: "1E293B",
  text: "F8FAFC",
  muted: "94A3B8",
  accent: "38BDF8",
  good: "34D399",
};

// Title slide
let s = pres.addSlide();
s.background = { color: C.bg };
s.addText("Q3 Strategy Review", {
  x: 0.6, y: 2.0, w: 8.8, h: 0.9,
  fontSize: 40, fontFace: "Arial", bold: true, color: C.text, margin: 0,
});
s.addText("Confidential  ·  August 2026", {
  x: 0.6, y: 3.0, w: 8.8, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: C.muted, margin: 0,
});

// Content slide — two column
s = pres.addSlide();
s.background = { color: C.bg };
s.addText("Key Results", {
  x: 0.5, y: 0.35, w: 9, h: 0.55,
  fontSize: 28, fontFace: "Arial", bold: true, color: C.text, margin: 0,
});

// Card
s.addShape(pres.ShapeType.roundRect, {
  x: 0.5, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.card }, rectRadius: 0.1,
});
s.addText("Revenue", {
  x: 0.75, y: 1.45, w: 3.8, h: 0.35,
  fontSize: 14, fontFace: "Arial", color: C.muted, margin: 0,
});
s.addText("$12.4M", {
  x: 0.75, y: 1.9, w: 3.8, h: 0.7,
  fontSize: 40, fontFace: "Arial", bold: true, color: C.good, margin: 0,
});
s.addText([
  { text: "Up 18% YoY", options: { breakLine: true } },
  { text: "Beat plan by $1.1M", options: { breakLine: true } },
  { text: "EMEA strongest region" },
], {
  x: 0.75, y: 2.8, w: 3.8, h: 1.6,
  fontSize: 15, fontFace: "Arial", color: C.text, valign: "top",
});

pres.writeFile({ fileName: "output.pptx" });
```

Layouts: `LAYOUT_16x9` (default, 10×5.625"), `LAYOUT_16x10`, `LAYOUT_4x3`, `LAYOUT_WIDE` (13.3×7.5").

- Full API patterns, charts, tables, and icons: [references/creating.md](references/creating.md)
- Design rules that separate pro decks from AI sludge: [references/design.md](references/design.md)

---

## Reading content

```bash
python -m markitdown deck.pptx
# structured
python - <<'PY'
from pptx import Presentation
prs = Presentation("deck.pptx")
for i, slide in enumerate(prs.slides, 1):
    print(f"--- Slide {i} ---")
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(shape.text_frame.text)
PY
```

---

## Editing existing decks

Prefer **python-pptx** for text swaps and light structural edits:

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation("template.pptx")
# Replace text in all shapes
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    if "[COMPANY]" in run.text:
                        run.text = run.text.replace("[COMPANY]", "Acme")
prs.save("output.pptx")
```

Preserve master layouts, theme colors, and existing images. Don't rebuild a branded template from scratch.

For native charts, prefer replacing data in place (`chart.replace_data(...)`) so placement and most
formatting survive. Reuse an existing slide layout for new slides. For animation-heavy slides,
externally linked charts, exact duplication, or other features `python-pptx` cannot round-trip,
prefer native PowerPoint automation when available and report the platform dependency.

---

## Hard pitfalls (corrupt or ugly output)

1. **No `#` in hex colors** — `"FF0000"` not `"#FF0000"`
2. **No 8-char hex for opacity** — use `opacity: 0.15` on shadows, not `"00000020"`
3. **Never unicode `•` bullets** — use `bullet: true`
4. **Use `breakLine: true`** between items in text arrays
5. **Fresh options objects** — PptxGenJS mutates shadow/fill objects; don't reuse one object across shapes
6. **Negative shadow offset corrupts files** — use `angle: 270` for upward shadows
7. **`margin: 0`** on text when aligning to shapes/lines
8. **Don't pair accent bars with `roundRect`** — corners won't cover; use `rect`

---

## QA (mandatory — assume first pass is wrong)

### Content

```bash
python scripts/qa_text.py output.pptx
python -m markitdown output.pptx | grep -iE 'lorem|ipsum|xxxx|placeholder|this (page|slide)|TODO|TBD'
```

`qa_text.py` must exit 0. List every issue it prints. Do not skip to visual QA while placeholders remain.

### Visual

Convert and **look at every slide as an image**:

```bash
python scripts/soffice.py --convert-to pdf --outdir out output.pptx
pdftoppm -jpeg -r 150 out/output.pdf slide
```

`scripts/soffice.py` finds `soffice` on PATH or the official Flatpak. Do not assume `soffice` is on PATH.

Hunt for:
- Overlaps, overflow, cut-off text
- Gaps < 0.3" or uneven spacing
- Margins < 0.5" from edges
- Low-contrast text/icons
- Misaligned columns
- Leftover placeholders
- Same layout repeated every slide (boring)

**Do not ship until you've done at least one fix → re-render cycle.**

---

## Dependencies

```bash
npm install -g pptxgenjs
pip install "markitdown[pptx]" python-pptx Pillow
# system: libreoffice, poppler-utils
```
