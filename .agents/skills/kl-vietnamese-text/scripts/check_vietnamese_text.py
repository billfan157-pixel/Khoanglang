#!/usr/bin/env python3
"""Check text files for Vietnamese encoding problems.

Usage:
    python check_vietnamese_text.py docs data tools [more paths ...]

Reports, per file:
    NOT_UTF8   the file is not valid UTF-8
    MOJIBAKE   UTF-8 text that was decoded with a legacy code page (e.g. "háº¿t" instead of "hết")
    NOT_NFC    text is not Unicode NFC (decomposed diacritics render and compare differently)
    BOM        file starts with a UTF-8 byte-order mark (WARN: breaks some JSON parsers)

Exit code: 0 = clean, 1 = findings, 2 = bad usage.
Skipped directories: .git, .agents (its docs quote mojibake on purpose), Content, Saved,
Intermediate, Binaries, DerivedDataCache, node_modules. Pass a file path to check a skipped file.
"""
import re
import sys
import unicodedata
from pathlib import Path

EXTENSIONS = {".md", ".txt", ".json", ".jsonc", ".csv", ".py", ".ps1", ".ini", ".yaml", ".yml"}
SKIP_DIRS = {".git", ".agents", "Content", "Saved", "Intermediate", "Binaries", "DerivedDataCache", "node_modules"}

# Typical signatures of UTF-8 bytes decoded as Windows-1252 / Latin-1.
# "Ã" alone is a legal Vietnamese capital (e.g. NGÃ), so only flag it before a symbol character.
MOJIBAKE = re.compile(
    "Ã[\u00a0-\u00bf]"                                   # à á ã â ê ô ... as "Ã " "Ã¡" "Ã£"
    "|Ä[\u0080-\u00bf\u02c6\u02dc\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u2018-\u203a]"  # đ Đ ă Ă
    "|áº|á»"                                              # ạ ả ấ ế ề ... (E1 BA/BB xx)
    "|â€"                                                 # curly quotes, dashes, ellipsis
    "|Æ[°¡]"                                              # ư ơ
    "|\ufffd"                                             # replacement character
)


def iter_files(paths):
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in EXTENSIONS \
                        and not (set(child.parts) & SKIP_DIRS):
                    yield child


def check(path: Path):
    findings = []
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        findings.append((1, "BOM", "UTF-8 byte-order mark at start of file"))
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return [(0, "NOT_UTF8", str(exc))]
    for number, line in enumerate(text.splitlines(), start=1):
        if MOJIBAKE.search(line):
            findings.append((number, "MOJIBAKE", line.strip()[:100]))
        elif line != unicodedata.normalize("NFC", line):
            findings.append((number, "NOT_NFC", line.strip()[:100]))
    return findings


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    total = 0
    checked = 0
    for path in iter_files(argv[1:]):
        checked += 1
        for number, code, detail in check(path):
            print(f"{path}:{number}: {code}: {detail}")
            if code != "BOM":
                total += 1
    print(f"{checked} file(s) checked, {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
