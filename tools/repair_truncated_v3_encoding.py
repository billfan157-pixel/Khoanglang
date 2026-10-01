#!/usr/bin/env python3
"""VERIFIER/REPAIRER: restore the 5 lost U+1ECD/U+1ED7 lead bytes in the truncated V3 file.

Usage:
    python tools/repair_truncated_v3_encoding.py --check
    python tools/repair_truncated_v3_encoding.py --apply

Why this exists
---------------
`docs/story/Khoang_Lang_02_17_Cot_truyen_v3_truncated_2026-09-29.md` is not valid
UTF-8. It fails at five places, always the same way: the 3-byte sequence for the
letter 'o-horn with dot' (U+1ECD, bytes E1 BB 8D) or 'o-horn with tilde'
(U+1ED7, bytes E1 BB 97) lost its leading 0xE1. So every affected word reads
'M<i>o</i>i' / 'M<i>o</i>' instead of 'Moi' / 'Mo'. That is a byte-level write
fault, not an authoring mistake: the file is UTF-8 everywhere else, has no BOM,
and is LF-only.

How the repair was justified
----------------------------
Every repaired position was cross-checked against
`docs/story/Khoang_Lang_02_17_Cot_truyen_v3_full_2026-09-29.md`, which is the
same document, clean, and valid UTF-8. All five repaired 34-character windows
appear verbatim in that file. So this restores the author's text; it does not
invent wording.

What this script does and does not touch
----------------------------------------
It touches exactly five bytes in exactly one file, and refuses to run unless
every one of those positions still holds the expected broken byte pair. It does
not re-encode, re-wrap, normalize, or reorder anything else, and it leaves
`docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md` (the live canon) byte-identical.

Safety properties
-----------------
- Idempotent: running --apply twice is a no-op the second time.
- Refuses to run if the file already decodes as UTF-8 (nothing to repair).
- Refuses to run if any expected broken position does not match, so a second
  partial edit cannot be silently compounded.
- Verifies the result decodes as UTF-8, is Unicode NFC, and reports the SHA256
  before and after.

Exit code: 0 = nothing to do or repair applied and verified, 1 = mismatch.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import unicodedata
from pathlib import Path

TARGET = Path("docs/story/Khoang_Lang_02_17_Cot_truyen_v3_truncated_2026-09-29.md")
REFERENCE = Path("docs/story/Khoang_Lang_02_17_Cot_truyen_v3_full_2026-09-29.md")

# (byte offset in the current broken file, expected trailing bytes, letter, expected word)
BROKEN = [
    (27979, b"\xbb\x8d", "U+1ECD", "Mọi"),
    (35556, b"\xbb\x97", "U+1ED7", "Mỗi"),
    (35983, b"\xbb\x8d", "U+1ECD", "Mọi"),
    (39409, b"\xbb\x97", "U+1ED7", "Mỗi"),
    (42957, b"\xbb\x97", "U+1ED7", "Mỗi"),
]
LEAD = b"\xe1"
WINDOW = 34


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def broken_offsets(data: bytes) -> list[int]:
    """Byte offsets where UTF-8 decoding fails, collapsed to one per run.

    A 3-byte sequence that lost its lead byte fails at two consecutive offsets:
    the orphaned byte and the continuation byte after it. Both are indistinguishable
    by bit pattern, because an orphaned 0xBB/0x97 still looks like 0b10xxxxxx.
    So failures are grouped into runs of consecutive offsets and only the first
    offset of each run is reported, which is the repair point.
    """
    failures, pos = [], 0
    while pos < len(data):
        try:
            data[pos:].decode("utf-8")
            break
        except UnicodeDecodeError as exc:
            failures.append(pos + exc.start)
            pos = pos + exc.start + 1
    runs: list[int] = []
    for offset in failures:
        if not runs or offset != runs[-1] + 1:
            runs.append(offset)
    return runs


def verify_layout(data: bytes) -> list[str]:
    """Return a list of problems; empty means the file is in the expected state."""
    problems = []
    actual = broken_offsets(data)
    expected = [offset for offset, _, _, _ in BROKEN]
    if actual != expected:
        problems.append(f"unexpected broken offsets: {actual} != {expected}")
    for offset, tail, letter, word in BROKEN:
        if data[offset:offset + 2] != tail:
            got = data[offset:offset + 2].hex()
            problems.append(f"offset {offset}: expected {tail.hex()}, got {got}")
            continue
        # The byte before must be an ASCII letter so the restored word is 'M' + letter.
        if offset < 1 or not chr(data[offset - 1]).isascii():
            problems.append(f"offset {offset}: byte before is not ASCII, refusing to guess a word")
            continue
        print(f"  offset {offset:>5}: 0x{tail.hex()} + preceding {chr(data[offset - 1])!r} -> {word} ({letter})")
    return problems


def cross_check(text: str) -> list[str]:
    """Confirm each repaired window appears verbatim in the clean full version."""
    if not REFERENCE.is_file():
        return [f"reference missing: {REFERENCE}"]
    reference = REFERENCE.read_text(encoding="utf-8")
    problems = []
    prefix_chars = []
    for offset, _, _, _ in BROKEN:
        prefix = text.encode("utf-8")[:offset]
        start = len(prefix.decode("utf-8")) - 1
        prefix_chars.append(text[start:start + WINDOW])
    for window in prefix_chars:
        if window not in reference:
            problems.append(f"window not found verbatim in the full version: {window!r}")
        else:
            print(f"  verbatim in full version: {window!r}")
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="diagnose only, write nothing")
    parser.add_argument("--apply", action="store_true", help="write the repaired file")
    args = parser.parse_args(argv[1:])
    if args.check == args.apply:
        parser.print_help()
        return 2

    if not TARGET.is_file():
        print(f"target missing: {TARGET}")
        return 1

    before = TARGET.read_bytes()
    print(f"target   : {TARGET}")
    print(f"sha256   : {sha256(before)}")

    if not broken_offsets(before):
        try:
            text = before.decode("utf-8")
        except UnicodeDecodeError as exc:  # pragma: no cover - contradicts the check
            print(f"unexpected: cannot decode: {exc}")
            return 1
        print("state    : already valid UTF-8, nothing to repair")
        print(f"nfc      : {unicodedata.is_normalized('NFC', text)}")
        return 0

    print("state    : broken, expected layout follows")
    problems = verify_layout(before)
    if problems:
        for problem in problems:
            print(f"REFUSED  : {problem}")
        return 1

    repaired = bytearray(before)
    for offset, _, _, _ in sorted(BROKEN, reverse=True):
        repaired[offset:offset] = LEAD
    repaired = bytes(repaired)

    try:
        text = repaired.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"REFUSED  : repair did not produce valid UTF-8: {exc}")
        return 1

    if not unicodedata.is_normalized("NFC", text):
        print("REFUSED  : repaired text is not NFC, leaving file alone")
        return 1

    print("cross-check against the clean full version:")
    problems = cross_check(text)
    if problems:
        for problem in problems:
            print(f"REFUSED  : {problem}")
        return 1

    print(f"after    : sha256 {sha256(repaired)} (+{len(repaired) - len(before)} bytes)")

    if args.check:
        print("check only, no write")
        return 0

    TARGET.write_bytes(repaired)
    print("APPLIED  : wrote 5 bytes")
    reread = TARGET.read_bytes()
    if reread != repaired:
        print("FAILED  : file on disk does not match what was written")
        return 1
    print("verified: file on disk matches")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))