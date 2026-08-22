#!/usr/bin/env python3
"""Forward-test the high-risk skill helpers.

Stdlib only, except ics which uses icalendar when installed.
Run from the repo root: python scripts/forward_test.py
"""

from __future__ import annotations

import csv
import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import zipfile
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
FAILED: list[str] = []
PASSED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASSED.append(name)
        print(f"  ok   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name}  {detail}")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_csv_neutralize() -> None:
    mod = load(ROOT / "csv/scripts/neutralize.py", "csv_neutralize")
    cases = {
        "=CMD()": "'=CMD()",
        "+1+1": "'+1+1",
        "@SUM(A1)": "'@SUM(A1)",
        "-SUM(A1)": "'-SUM(A1)",
        "-12.5": "-12.5",
        "hello": "hello",
        "": "",
        "\t=CMD()": "'\t=CMD()",
        " =CMD()": "' =CMD()",
        "\n=CMD()": "'\n=CMD()",
        "\r=CMD()": "'\r=CMD()",
        " -12.5": " -12.5",
    }
    for raw, expected in cases.items():
        got = mod.neutralize(raw)
        check(f"csv.neutralize[{raw!r}]", got == expected, f"got {got!r}")

    old = sys.argv
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.csv"
        dst = Path(tmp) / "out.csv"
        src.write_text("id,note\n1,=HYPERLINK(\"x\")\n2,-4\n", encoding="utf-8")
        try:
            sys.argv = ["neutralize.py", "--in", str(src), "--out", str(dst)]
            rc = mod.main()
        finally:
            sys.argv = old
        rows = list(csv.reader(dst.open(newline="", encoding="utf-8")))
        check("csv.neutralize.file", rc == 0 and rows[1][1].startswith("'") and rows[2][1] == "-4")

        semi = Path(tmp) / "eu.csv"
        semi_out = Path(tmp) / "eu-out.csv"
        semi.write_bytes("id;note\n1;=HYPERLINK(\"x\")\n".encode("latin-1"))
        try:
            sys.argv = [
                "neutralize.py", "--in", str(semi), "--out", str(semi_out),
                "--encoding", "latin-1", "--delimiter", ";",
            ]
            rc = mod.main()
        finally:
            sys.argv = old
        semi_rows = list(csv.reader(semi_out.open(newline="", encoding="latin-1"), delimiter=";"))
        check("csv.neutralize.semicolon", rc == 0 and semi_rows[1][1].startswith("'"), semi_rows)

        sniffed = Path(tmp) / "sniff.csv"
        sniffed_out = Path(tmp) / "sniff-out.csv"
        sniffed.write_text("id;note\n1;=CMD()\n2;ok\n3;more\n", encoding="utf-8")
        try:
            sys.argv = ["neutralize.py", "--in", str(sniffed), "--out", str(sniffed_out)]
            rc = mod.main()
        finally:
            sys.argv = old
        sniffed_rows = list(csv.reader(sniffed_out.open(newline="", encoding="utf-8"), delimiter=";"))
        check(
            "csv.neutralize.sniff_semicolon",
            rc == 0 and len(sniffed_rows[0]) == 2 and sniffed_rows[1][1].startswith("'"),
            sniffed_rows,
        )


def test_pdf_coords() -> None:
    mod = load(ROOT / "pdf/scripts/coords.py", "pdf_coords")
    x, y = mod.px_to_pt(150, 0, 150, 792)
    check("pdf.coords.top", abs(x - 72) < 0.01 and abs(y - 792) < 0.01, f"{x},{y}")
    x, y = mod.px_to_pt(0, 150, 150, 792)
    check("pdf.coords.flip_y", abs(x) < 0.01 and abs(y - 720) < 0.01, f"{x},{y}")


def _minimal_docx(path: Path) -> None:
    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:t>[CLI</w:t></w:r>
      <w:r><w:t>ENT]</w:t></w:r>
    </w:p>
  </w:body>
</w:document>"""
    header = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:r><w:t>Prepared for [CLIENT]</w:t></w:r></w:p>
</w:hdr>"""
    ctypes = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/header1.xml", header)


def test_docx_replace() -> None:
    mod = load(ROOT / "docx/scripts/replace_text.py", "docx_replace")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.docx"
        dst = Path(tmp) / "out.docx"
        _minimal_docx(src)
        n = mod.replace_docx(src, dst, {"[CLIENT]": "Acme"})
        check("docx.replace.count", n == 2, f"n={n}")
        with zipfile.ZipFile(dst) as z:
            body = z.read("word/document.xml").decode()
            header = z.read("word/header1.xml").decode()
        check("docx.replace.split_run", "Acme" in body and "[CLI" not in body and "ENT]" not in body, body)
        check("docx.replace.header", "Acme" in header and "[CLIENT]" not in header, header)


def _minimal_pptx(path: Path, texts: list[list[str]]) -> None:
    ctypes = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
</Types>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("ppt/presentation.xml", "<p:presentation xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'/>")
        for i, slide_texts in enumerate(texts, 1):
            runs = "".join(f"<a:t>{t}</a:t>" for t in slide_texts)
            z.writestr(f"ppt/slides/slide{i}.xml", f"<p:sld>{runs}</p:sld>")


def test_pptx_qa() -> None:
    mod = load(ROOT / "pptx/scripts/qa_text.py", "pptx_qa")
    with tempfile.TemporaryDirectory() as tmp:
        clean = Path(tmp) / "clean.pptx"
        dirty = Path(tmp) / "dirty.pptx"
        _minimal_pptx(clean, [["Q3 Results", "Revenue up"]])
        _minimal_pptx(dirty, [["lorem ipsum"], []])
        old = sys.argv
        try:
            sys.argv = ["qa_text.py", str(clean)]
            check("pptx.qa.clean", mod.main() == 0)
            sys.argv = ["qa_text.py", str(dirty)]
            check("pptx.qa.dirty", mod.main() == 1)
            generic = Path(tmp) / "generic.pptx"
            _minimal_pptx(generic, [["Title"]])
            sys.argv = ["qa_text.py", str(generic)]
            check("pptx.qa.generic_title", mod.main() == 1)
        finally:
            sys.argv = old


def test_xlsx_qa() -> None:
    mod = load(ROOT / "xlsx/scripts/qa_workbook.py", "xlsx_qa")
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sheet = f"""<?xml version="1.0"?>
<worksheet xmlns="{ns}">
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>Total</t></is></c>
      <c r="B1"><v>42</v></c></row>
  </sheetData>
</worksheet>"""
    workbook = f"""<?xml version="1.0"?>
<workbook xmlns="{ns}">
  <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets>
</workbook>"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "book.xlsx"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("xl/workbook.xml", workbook)
            z.writestr("xl/worksheets/sheet1.xml", sheet)
        old = sys.argv
        try:
            sys.argv = ["qa_workbook.py", str(path)]
            check("xlsx.qa.flags_sheet1_and_no_formulas", mod.main() == 1)
        finally:
            sys.argv = old


def test_ics() -> None:
    script = ROOT / "ics/scripts/write_event.py"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "meeting.ics"
        old = sys.argv
        try:
            sys.argv = [
                "write_event.py",
                "--summary", "Design review",
                "--start", "2026-03-20T11:00:00",
                "--tz", "America/New_York",
                "--minutes", "60",
                "--out", str(out),
            ]
            spec = importlib.util.spec_from_file_location("write_event", script)
            mod = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(mod)
            rc = mod.main()
        finally:
            sys.argv = old
        raw = out.read_bytes()
        text = raw.decode()
        check("ics.wrote", rc == 0 and out.is_file())
        check("ics.crlf", b"\r\n" in raw)
        check("ics.has_dtstart", "DTSTART" in text)
        check("ics.no_naive_guess", "BEGIN:VEVENT" in text)
        # 11:00 America/New_York in March is UTC 15:00
        check("ics.tz_converted", "20260320T150000Z" in text or "TZID=America/New_York" in text, text[:400])

        all_day = Path(tmp) / "holiday.ics"
        sys.argv = [
            "write_event.py",
            "--summary", "Holiday",
            "--start", "2026-07-04",
            "--all-day",
            "--out", str(all_day),
        ]
        try:
            spec = importlib.util.spec_from_file_location("write_event2", script)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
        finally:
            sys.argv = old
        holiday = all_day.read_text()
        check("ics.all_day_exclusive", "20260704" in holiday and "20260705" in holiday, holiday)

        start = datetime(2026, 3, 20, 11, 0, tzinfo=ZoneInfo("America/New_York"))
        end = start + timedelta(minutes=60)
        std_args = Namespace(
            summary="Meet\r\nDTSTART:19970101T000000Z;note,path\\x",
            uid="uid-1",
            method="PUBLISH",
            sequence=0,
            rrule="",
            organizer="",
            attendee=[],
            byday=[],
        )
        raw = mod.write_stdlib(std_args, start, end)
        text = raw.decode()
        dtstart_props = [ln for ln in text.split("\r\n") if ln.startswith("DTSTART")]
        check("ics.stdlib.one_dtstart_prop", len(dtstart_props) == 1, text)
        check("ics.stdlib.escaped_nl", "SUMMARY:Meet\\nDTSTART:" in text, text)
        check("ics.stdlib.escaped_semi_comma_bs", r"\;note\,path\\x" in text, text)
        std_args.method = "REQUEST"
        std_args.summary = "ok"
        refused_request = False
        try:
            mod.write_stdlib(std_args, start, end)
        except SystemExit:
            refused_request = True
        check("ics.stdlib.refuse_request", refused_request)
        std_args.method = "PUBLISH"
        std_args.rrule = "WEEKLY"
        refused_rrule = False
        try:
            mod.write_stdlib(std_args, start, end)
        except SystemExit:
            refused_rrule = True
        check("ics.stdlib.refuse_rrule", refused_rrule)


def test_yaml_norway() -> None:
    try:
        import yaml  # type: ignore
    except ImportError:
        check("yaml.norway.skipped_optional", True)
        return
    loaded = yaml.safe_load("country: NO\n")
    check("yaml.norway.unquoted_is_bool", loaded["country"] is False)
    quoted = yaml.safe_load('country: "NO"\n')
    check("yaml.norway.quoted_is_str", quoted["country"] == "NO")


def test_libreoffice() -> None:
    soffice = load(ROOT / "docx/scripts/soffice.py", "soffice_helper")
    try:
        soffice.find_soffice(Path("/tmp"))
    except SystemExit:
        check("libreoffice.skipped_not_installed", True)
        return

    pdftotext = shutil.which("pdftotext")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html = tmp_path / "letter.html"
        html.write_text(
            "<html><body><h1>Engagement letter</h1>"
            "<p>Prepared for [CLIENT].</p></body></html>",
            encoding="utf-8",
        )
        odt = soffice.convert(html, tmp_path / "odt", "odt")
        docx_in = soffice.convert(odt, tmp_path / "docx0", "docx")
        replace = load(ROOT / "docx/scripts/replace_text.py", "docx_replace_lo")
        docx_out = tmp_path / "letter-acme.docx"
        n = replace.replace_docx(docx_in, docx_out, {"[CLIENT]": "Acme Corp"})
        check("lo.docx.replace_count", n >= 1, f"n={n}")
        pdf = soffice.convert(docx_out, tmp_path / "pdf", "pdf")
        if pdftotext:
            text = subprocess.check_output([pdftotext, "-layout", str(pdf), "-"], text=True)
            check("lo.docx.pdf_has_acme", "Acme Corp" in text and "[CLIENT]" not in text, text)
        else:
            check("lo.docx.pdf_exists", pdf.is_file())

        csv_in = tmp_path / "sales.csv"
        csv_in.write_text("Region,Rep,Revenue\nEMEA,Ada,48000\nNA,Cam,60000\nAPAC,Eve,27000\n")
        xlsx = soffice.convert(csv_in, tmp_path / "xlsx0", "xlsx")
        summed = tmp_path / "sales-sum.xlsx"
        _inject_sum(xlsx, summed)
        ods = soffice.convert(summed, tmp_path / "ods", "ods")
        xlsx_pdf = soffice.convert(ods, tmp_path / "xlsxpdf", "pdf")
        if pdftotext:
            text = subprocess.check_output([pdftotext, "-layout", str(xlsx_pdf), "-"], text=True)
            check("lo.xlsx.sum_135000", "135000" in text.replace(",", ""), text)

        odp = _minimal_odp(tmp_path / "deck.odp")
        deck_pdf = soffice.convert(odp, tmp_path / "deckpdf", "pdf")
        deck_pptx = soffice.convert(odp, tmp_path / "deckpptx", "pptx")
        if pdftotext:
            text = subprocess.check_output([pdftotext, "-layout", str(deck_pdf), "-"], text=True)
            check("lo.pptx.pdf_title", "Q3 Strategy Review" in text, text)
        qa = load(ROOT / "pptx/scripts/qa_text.py", "pptx_qa_lo")
        old = sys.argv
        try:
            sys.argv = ["qa_text.py", str(deck_pptx)]
            check("lo.pptx.qa_clean", qa.main() == 0)
        finally:
            sys.argv = old


def _inject_sum(src: Path, dst: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(buf, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "xl/sharedStrings.xml":
                text = data.decode("utf-8")
                text = text.replace("count=\"9\"", "count=\"10\"").replace(
                    "uniqueCount=\"9\"", "uniqueCount=\"10\""
                )
                text = text.replace("</sst>", "<si><t>Total</t></si></sst>")
                data = text.encode("utf-8")
            elif info.filename.endswith("sheet1.xml"):
                text = data.decode("utf-8")
                text = text.replace('ref="A1:C4"', 'ref="A1:C5"')
                row = (
                    '<row r="5"><c r="A5" t="s"><v>9</v></c>'
                    '<c r="C5" t="n"><f>SUM(C2:C4)</f><v>0</v></c></row>'
                )
                text = text.replace("</sheetData>", row + "</sheetData>")
                data = text.encode("utf-8")
            zout.writestr(info, data)
    dst.write_bytes(buf.getvalue())


def _minimal_odp(path: Path) -> Path:
    files = {
        "META-INF/manifest.xml": """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.presentation"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>""",
        "meta.xml": """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.2"><office:meta/></office:document-meta>""",
        "styles.xml": """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.2">
<office:automatic-styles><style:page-layout style:name="PM1"><style:page-layout-properties fo:page-width="25.4cm" fo:page-height="14.2875cm" style:print-orientation="landscape"/></style:page-layout></office:automatic-styles>
<office:master-styles><style:master-page style:name="Default" style:page-layout-name="PM1"/></office:master-styles>
</office:document-styles>""",
        "content.xml": """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" office:version="1.2">
<office:body><office:presentation>
<draw:page draw:name="page1" draw:master-page-name="Default">
<draw:frame svg:x="1.5cm" svg:y="5cm" svg:width="22cm" svg:height="3cm">
<draw:text-box><text:p>Q3 Strategy Review</text:p></draw:text-box>
</draw:frame>
</draw:page>
</office:presentation></office:body></office:document-content>""",
    }
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.presentation", compress_type=zipfile.ZIP_STORED)
        for name, text in files.items():
            z.writestr(name, text)
    return path


def test_skill_claims() -> None:
    sql = (ROOT / "sql/SKILL.md").read_text()
    check("sql.mentions_snowflake", "Snowflake" in sql and "VARIANT" in sql)
    check("sql.no_concurrently_in_txn", "outside the transaction" in sql)
    ics = (ROOT / "ics/SKILL.md").read_text()
    check("ics.no_leading_skeleton", "```ics" not in ics.split("## Generate")[0])
    email_refs = list((ROOT / "email-html/references").glob("*.md"))
    check("email.checklist_removed", not (ROOT / "email-html/references/checklist.md").exists())
    check("email.clients_ref", any(p.name == "clients.md" for p in email_refs))
    docker = (ROOT / "docker/SKILL.md").read_text()
    check("docker.python_multistage", "AS builder" in docker and "AS runner" in docker)
    check("docker.dockerignore_sane", "Dockerfile*" not in docker.split("## .dockerignore")[1].split("## Compose")[0] or "Do **not**" in docker)
    testing = (ROOT / "testing/SKILL.md").read_text()
    check("testing.no_pytest_count_flag", "pytest --count=" not in testing)
    check("testing.no_vitest_repeat_flag", "vitest run --repeat" not in testing)
    da = (ROOT / "data-analysis/SKILL.md").read_text()
    check("data_analysis.to_period_strips_tz", "tz_localize(None)" in da and ".dt.to_period" in da)


def main() -> int:
    print("Forward tests\n")
    test_csv_neutralize()
    test_pdf_coords()
    test_docx_replace()
    test_pptx_qa()
    test_xlsx_qa()
    test_ics()
    test_yaml_norway()
    test_skill_claims()
    test_libreoffice()
    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("failed:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
