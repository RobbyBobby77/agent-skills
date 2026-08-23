#!/usr/bin/env python3
"""Write a timezone-aware .ics and parse it back.

Prefers the icalendar package. Without it, emits a single UTC or all-day
event only — recurrence, METHOD:REQUEST, and VTIMEZONE require icalendar.

Usage:
  python scripts/write_event.py --summary "Design review" \\
    --start 2026-03-20T11:00:00 --tz America/New_York --minutes 60 \\
    --out meeting.ics
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def _parse_start(value: str, tz_name: str | None, all_day: bool):
    if all_day:
        return date.fromisoformat(value[:10])
    naive = datetime.fromisoformat(value)
    if naive.tzinfo is not None:
        return naive
    if not tz_name:
        raise SystemExit("refusing to write a naive local time: pass --tz or --all-day")
    return naive.replace(tzinfo=ZoneInfo(tz_name))


def write_with_library(args, start, end) -> bytes:
    from icalendar import Calendar, Event, vCalAddress

    cal = Calendar()
    cal.add("prodid", "-//agent-skills//ics//EN")
    cal.add("version", "2.0")
    cal.add("method", args.method)
    ev = Event()
    ev.add("uid", args.uid or f"{uuid.uuid4()}@agent-skills")
    ev.add("dtstamp", datetime.now(tz=timezone.utc))
    ev.add("dtstart", start)
    ev.add("dtend", end)
    ev.add("summary", args.summary)
    ev.add("status", "CANCELLED" if args.method == "CANCEL" else "CONFIRMED")
    ev.add("sequence", args.sequence)
    if args.organizer:
        ev["organizer"] = vCalAddress(args.organizer)
    for attendee in args.attendee:
        ev.add("attendee", vCalAddress(attendee), encode=0)
    if args.rrule:
        ev.add("rrule", {"freq": args.rrule, "byday": args.byday or None})
    cal.add_component(ev)
    return cal.to_ical()


def _fmt_dt(dt: datetime) -> str:
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y%m%dT%H%M%SZ")


def escape_text(value: str) -> str:
    """RFC 5545 TEXT: backslash, semicolon, comma, then CR/LF → \\\\n."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def _utf8_prefix(data: bytes, max_octets: int) -> int:
    """Largest valid-UTF-8 prefix of data that is at most max_octets long."""
    if len(data) <= max_octets:
        return len(data)
    cut = max_octets
    while cut > 0 and data[cut] & 0xC0 == 0x80:
        cut -= 1
    if cut == 0:
        cut = 1
        while cut < len(data) and data[cut] & 0xC0 == 0x80:
            cut += 1
    return cut


def fold_line(line: str, limit: int = 75) -> list[str]:
    """RFC 5545 §3.1: physical lines at most `limit` octets, continuations start with SPACE."""
    remaining = line.encode("utf-8")
    if len(remaining) <= limit:
        return [line]
    physical: list[str] = []
    first = True
    while remaining:
        budget = limit if first else limit - 1  # continuation lines include a leading SPACE
        cut = _utf8_prefix(remaining, budget)
        chunk, remaining = remaining[:cut], remaining[cut:]
        text = chunk.decode("utf-8")
        physical.append(text if first else " " + text)
        first = False
    return physical


def fold_ics(lines: list[str], limit: int = 75) -> bytes:
    physical: list[str] = []
    for line in lines:
        physical.extend(fold_line(line, limit=limit))
    return "\r\n".join(physical).encode("utf-8")


def write_stdlib(args, start, end) -> bytes:
    if args.rrule:
        raise SystemExit("recurrence requires the icalendar package")
    if args.method == "REQUEST":
        raise SystemExit("METHOD:REQUEST requires the icalendar package")
    if args.organizer or args.attendee:
        raise SystemExit("organizer/attendees require the icalendar package")
    uid = escape_text(args.uid or f"{uuid.uuid4()}@agent-skills")
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if isinstance(start, date) and not isinstance(start, datetime):
        dtstart = f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}"
        dtend = f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}"
    else:
        dtstart = f"DTSTART:{_fmt_dt(start)}"
        dtend = f"DTEND:{_fmt_dt(end)}"
    status = "CANCELLED" if args.method == "CANCEL" else "CONFIRMED"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//agent-skills//ics//EN",
        f"METHOD:{args.method}",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        dtstart,
        dtend,
        f"SUMMARY:{escape_text(args.summary)}",
        f"STATUS:{status}",
        f"SEQUENCE:{args.sequence}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return fold_ics(lines)


def parse_back(raw: bytes) -> None:
    try:
        from icalendar import Calendar

        cal = Calendar.from_ical(raw)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        if not events:
            raise SystemExit("round-trip parse found no VEVENT")
        ev = events[0]
        start = ev.decoded("dtstart")
        if start is None:
            raise SystemExit("round-trip parse missing DTSTART")
        print("parsed", ev.get("uid"), start, ev.get("sequence"))
        return
    except ImportError:
        text = raw.decode("utf-8")
        if "BEGIN:VEVENT" not in text or "DTSTART" not in text:
            raise SystemExit("stdlib sanity check failed")
        print("parsed (stdlib)", "DTSTART" in text)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--summary", required=True)
    p.add_argument("--start", required=True, help="ISO date or datetime")
    p.add_argument("--tz", dest="tz_name", default=None)
    p.add_argument("--minutes", type=int, default=60)
    p.add_argument("--all-day", action="store_true")
    p.add_argument("--method", default="PUBLISH", choices=["PUBLISH", "REQUEST", "CANCEL"])
    p.add_argument("--organizer", default="")
    p.add_argument("--attendee", action="append", default=[])
    p.add_argument("--rrule", default="", help="e.g. WEEKLY (requires icalendar)")
    p.add_argument("--byday", action="append", default=[])
    p.add_argument("--uid", default="")
    p.add_argument("--sequence", type=int, default=0)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    start = _parse_start(args.start, args.tz_name, args.all_day)
    if args.all_day:
        end = start + timedelta(days=1)
    else:
        end = start + timedelta(minutes=args.minutes)

    try:
        raw = write_with_library(args, start, end)
    except ImportError:
        raw = write_stdlib(args, start, end)

    path = Path(args.out)
    path.write_bytes(raw)
    parse_back(raw)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
