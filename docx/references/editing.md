# Editing Existing DOCX / DOTX Templates

**If a template is attached, EDIT IT. Never recreate with docx-js.**

## Workflow

```
unpack → inspect → replace text/fields → repack → visual QA
```

### Unpack / repack (OOXML)

```bash
# Unpack (works for .docx and .dotx)
unzip -q template.docx -d unpacked/
# or use a pretty-print unpacker if available in the environment

# After edits, rezip carefully — [Content_Types].xml must be first entry:
cd unpacked && zip -r -X ../output.docx [Content_Types].xml _rels word docProps
```

Better: use a pack/unpack helper if present in the environment; otherwise:

```python
# pack_docx.py — minimal safe repack
import zipfile, os, sys
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    # Content_Types first
    ct = os.path.join(src, "[Content_Types].xml")
    z.write(ct, "[Content_Types].xml")
    for root, _, files in os.walk(src):
        for f in files:
            path = os.path.join(root, f)
            arc = os.path.relpath(path, src)
            if arc == "[Content_Types].xml":
                continue
            z.write(path, arc)
```

### Inspect

```bash
pandoc template.docx -t plain | head -200
python -m markitdown template.docx
# list media
unzip -l template.docx | grep word/media
```

### Replace text safely

Word splits runs unpredictably (`Hel` + `lo`). Do **not** sed a single `<w:t>Hello</w:t>` and expect it to match.

**Strategy A — python-docx** (simple whole-paragraph / cell replacements):

```python
from docx import Document

doc = Document("template.docx")

def replace_in_paragraph(p, mapping):
    full = p.text
    for old, new in mapping.items():
        if old in full:
            full = full.replace(old, new)
    if full != p.text:
        # wipe runs and write one run (may lose mixed formatting inside the paragraph)
        for r in p.runs:
            r.text = ""
        if p.runs:
            p.runs[0].text = full
        else:
            p.add_run(full)

mapping = {"[CLIENT]": "Acme Corp", "[DATE]": "March 15, 2026"}

for p in doc.paragraphs:
    replace_in_paragraph(p, mapping)
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                replace_in_paragraph(p, mapping)
for section in doc.sections:
    for part in (section.header, section.footer):
        for p in part.paragraphs:
            replace_in_paragraph(p, mapping)

doc.save("output.docx")
```

**Strategy B — XML-level** when you must preserve complex run formatting: concatenate all `w:t` in a paragraph, locate the match across run boundaries, then rewrite runs. Prefer a battle-tested replace script over hand-rolled XML.

### Headers & footers

They live in separate parts (`word/header1.xml`, `word/footer1.xml`). Always process them — body-only edits leave stale template placeholders.

### Tracked changes (redlines)

```xml
<!-- Insertion -->
<w:ins w:id="1" w:author="Agent" w:date="2026-01-01T00:00:00Z">
  <w:r><w:t>new text</w:t></w:r>
</w:ins>

<!-- Deletion — use w:delText, not w:t -->
<w:del w:id="2" w:author="Agent" w:date="2026-01-01T00:00:00Z">
  <w:r><w:delText>old text</w:delText></w:r>
</w:del>
```

Minimal edits only — mark the changed span, not the whole sentence.

Accept all changes via LibreOffice when you need a clean final:

```bash
soffice --headless --accept="TrackChanges:AcceptAll" --convert-to docx input.docx
# or python-docx / specialized accept script if available
```

### Comments

Comments need coordinated updates across `word/comments.xml`, document markers, and relationships. Prefer a helper script; if writing XML by hand:

- `w:commentRangeStart` / `w:commentRangeEnd` are **siblings of** `w:r`, never inside a run
- Follow range end with a `w:commentReference` run

### Smart quotes

When injecting new text into XML, use entities for professional typography:

| Entity | Char |
|--------|------|
| `&#x2018;` `&#x2019;` | ‘ ’ |
| `&#x201C;` `&#x201D;` | “ ” |

### Whitespace

Add `xml:space="preserve"` on `<w:t>` nodes that have leading/trailing spaces.

### Pitfalls

- Never recreate a branded template from scratch
- Never sed only body text — headers/footers/text boxes hide placeholders
- Grepping for placeholder strings can miss split runs
- `.dotx` unpacks like `.docx`; don't force-convert first unless a tool requires it
- After repack, open/convert once to confirm the file isn't corrupt
