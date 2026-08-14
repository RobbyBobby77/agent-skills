---
name: docx
description: >
  Create, read, edit, and analyze Word documents (.docx, .dotx). Use when the user
  mentions Word, .docx, .dotx, reports, memos, letters, letterheads, contracts,
  proposals, resumes, or any professional document deliverable. Covers creation
  with docx-js, template filling, tracked changes, comments, tables, headers/footers,
  TOC, images, and conversion to PDF/images. Do NOT use for PDFs, spreadsheets,
  or presentations.
---

# Word Documents (DOCX)

A `.docx` is a ZIP of XML. Prefer high-level libraries for creation; unpack only when editing templates or doing tracked changes.

## Related skills

| Need | Skill |
|------|-------|
| PDF conversion / forms | `pdf` |
| Spreadsheet | `xlsx` |
| Slides | `pptx` |

## Workflow

1. Preserve the input and identify whether the task is creation, light editing, template filling, or OOXML surgery.
2. Inspect document text, sections, styles, headers/footers, tables, media, comments, and tracked changes as relevant.
3. Make the smallest change with the highest-level tool that preserves required features.
4. Reopen or extract the result to verify content, then convert and visually inspect every page.
5. Deliver a new output file unless the user explicitly requests replacement.

## Tool choice

| Task | Tool |
|------|------|
| Create from scratch | **docx-js** (`npm i docx`) |
| Fill / edit a template | `scripts/replace_text.py` (see [references/editing.md](references/editing.md)) |
| Extract text | `pandoc file.docx -t markdown` or `python -m markitdown file.docx` |
| Convert to PDF | `python scripts/soffice.py --convert-to pdf --outdir out file.docx` |
| Visual QA | PDF then `pdftoppm -jpeg -r 150 file.pdf page` |

**If a `.docx` / `.dotx` template is provided: edit it. Never recreate from scratch** — you will lose styles, headers, media, and theme colors.

---

## Create from scratch (docx-js)

```bash
npm install docx
```

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat } = require("docx");
const fs = require("fs");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } }, // 11pt
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F4E79" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E75B6" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }]},
      { reference: "numbers", levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }]},
    ],
  },
  sections: [{
    properties: {
      page: {
        // US Letter — docx-js defaults to A4; always set explicitly
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }, // 1"
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        children: [new TextRun({ text: "Company Name", italics: true, size: 18, color: "666666" })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", size: 18 }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
        ],
      })] }),
    },
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Title")] }),
      new Paragraph({ spacing: { after: 200 }, children: [
        new TextRun("Body copy. Never put \\n in a run — use separate Paragraphs."),
      ]}),
      new Paragraph({ numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Bullet item")] }),
      new Paragraph({ children: [new PageBreak()] }),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [4680, 4680],
        rows: [
          new TableRow({ children: [
            cell("Header A", true), cell("Header B", true),
          ]}),
          new TableRow({ children: [
            cell("Value 1"), cell("Value 2"),
          ]}),
        ],
      }),
    ],
  }],
});

function cell(text, header = false) {
  return new TableCell({
    borders,
    width: { size: 4680, type: WidthType.DXA },
    shading: header ? { fill: "1F4E79", type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [
      new TextRun({ text, bold: header, color: header ? "FFFFFF" : "333333", size: 20 }),
    ]})],
  });
}

Packer.toBuffer(doc).then((buf) => fs.writeFileSync("output.docx", buf));
```

### Page sizes (DXA, 1440 = 1")

| Paper | Width | Height | Content width @ 1" margins |
|-------|------:|-------:|---------------------------:|
| US Letter | 12240 | 15840 | 9360 |
| A4 | 11906 | 16838 | 9026 |

Landscape: pass portrait dimensions + `orientation: PageOrientation.LANDSCAPE` (docx-js swaps them).

---

## Critical rules

1. **Never unicode bullets** (`•` in text) — use `LevelFormat.BULLET` numbering config
2. **Never `\n` in runs** — separate `Paragraph` elements
3. **PageBreak must be inside a Paragraph**
4. **Tables need dual widths** — `columnWidths` on table AND `width` on every cell; both DXA; table width = sum of columns
5. **Use `WidthType.DXA`** — percentages break in Google Docs
6. **Use `ShadingType.CLEAR`** — never SOLID (black backgrounds)
7. **Always set page size** — default is A4
8. **Images** — `ImageRun` needs `type` + `data` (bytes), not a path; preserve aspect ratio
9. **Heading styles** — override with exact ids `Heading1`, `Heading2` and set `outlineLevel` for TOC
10. **Don't use tables as horizontal rules** — use paragraph bottom border instead

### Images

```javascript
const { ImageRun } = require("docx");
const png = fs.readFileSync("chart.png");
// preserve aspect ratio
const maxW = 450, ow = 1200, oh = 800;
const h = Math.round(maxW * (oh / ow));

new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new ImageRun({
    type: "png",
    data: png,
    transformation: { width: maxW, height: h },
    altText: { name: "Chart", description: "Revenue by quarter", title: "Revenue" },
  })],
});
```

### Headers / footers / page numbers

Already shown above. For two-column footers use tab stops, not tables.

### TOC

```javascript
const { TableOfContents } = require("docx");
// Headings must use HeadingLevel (not custom styles only)
new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" })
```

---

## Reading content

```bash
pandoc document.docx -t markdown -o out.md
pandoc --track-changes=all document.docx -t markdown   # include tracked changes
python -m markitdown document.docx
```

Legacy `.doc` → `.docx` first:

```bash
python scripts/soffice.py --convert-to docx --outdir out legacy.doc
```

---

## Editing existing / templates

Read [references/editing.md](references/editing.md) before touching a template.

Word splits runs mid-word (`Hel` + `lo`). Do not sed a single `<w:t>`. Use the shipped script — it searches headers/footers and concatenated runs:

```bash
python scripts/replace_text.py template.docx output.docx \
  --map replacements.json
# or
python scripts/replace_text.py template.docx output.docx \
  --match '[CLIENT]' --text 'Acme Corp'
```

Do not recreate a branded template with docx-js.

---

## Visual QA (required for created or modified docs)

1. Convert to PDF, then images
2. Check: margins, table alignment, orphan headings, header/footer collisions, low contrast, leftover placeholders (`lorem`, `XXXX`, `TODO`)
3. Fix and re-render until clean

```bash
python scripts/soffice.py --convert-to pdf --outdir out output.docx
pdftoppm -jpeg -r 150 out/output.pdf preview
```

`scripts/soffice.py` finds `soffice` on PATH or the official Flatpak (`org.libreoffice.LibreOffice`). Do not assume `soffice` is on PATH.

---

## Dependencies

```bash
npm install docx
# optional but recommended
pip install markitdown
# system: pandoc, libreoffice, poppler-utils (pdftoppm)
```
