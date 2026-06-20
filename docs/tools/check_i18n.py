from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Entry:
    msgid: str
    msgstr: str
    fuzzy: bool


def _read_po_string(lines: list[str], index: int, prefix: str) -> tuple[str, int]:
    value = ast.literal_eval(lines[index][len(prefix) :].strip())
    index += 1
    while index < len(lines) and lines[index].startswith('"'):
        value += ast.literal_eval(lines[index])
        index += 1
    return value, index


def parse_catalog(path: Path) -> list[Entry]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[Entry] = []
    fuzzy = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("#, fuzzy"):
            fuzzy = True
            index += 1
            continue
        if line.startswith("msgid "):
            msgid, index = _read_po_string(lines, index, "msgid ")
            if index >= len(lines) or not lines[index].startswith("msgstr "):
                raise ValueError(f"Missing msgstr after msgid in {path}: {msgid!r}")
            msgstr, index = _read_po_string(lines, index, "msgstr ")
            if msgid:
                entries.append(Entry(msgid=msgid, msgstr=msgstr, fuzzy=fuzzy))
            fuzzy = False
            continue
        if not line.strip():
            fuzzy = False
        index += 1
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Sphinx i18n catalog sync.")
    parser.add_argument("pot_dir", type=Path)
    parser.add_argument("po_dir", type=Path)
    args = parser.parse_args()

    failures: list[str] = []
    for pot_path in sorted(args.pot_dir.glob("*.pot")):
        po_path = args.po_dir / pot_path.with_suffix(".po").name
        if not po_path.exists():
            failures.append(f"Missing translation catalog: {po_path}")
            continue

        pot_entries = parse_catalog(pot_path)
        po_entries = parse_catalog(po_path)
        pot_msgids = {entry.msgid for entry in pot_entries}
        po_by_msgid = {entry.msgid: entry for entry in po_entries}

        missing = sorted(pot_msgids - po_by_msgid.keys())
        extra = sorted(po_by_msgid.keys() - pot_msgids)
        empty = sorted(
            entry.msgid
            for entry in po_entries
            if entry.msgid in pot_msgids and not entry.msgstr.strip()
        )
        fuzzy = sorted(
            entry.msgid
            for entry in po_entries
            if entry.msgid in pot_msgids and entry.fuzzy
        )

        for msgid in missing:
            failures.append(f"{po_path}: missing msgid {msgid!r}")
        for msgid in extra:
            failures.append(f"{po_path}: stale msgid {msgid!r}")
        for msgid in empty:
            failures.append(f"{po_path}: empty msgstr for {msgid!r}")
        for msgid in fuzzy:
            failures.append(f"{po_path}: fuzzy translation for {msgid!r}")

    if failures:
        for failure in failures:
            sys.stderr.write(f"{failure}\n")
        return 1

    sys.stdout.write("Sphinx i18n catalogs are synchronized.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
