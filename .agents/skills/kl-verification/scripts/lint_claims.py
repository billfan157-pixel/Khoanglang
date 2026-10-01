#!/usr/bin/env python3
"""Lint status/evidence markdown for unlabeled or over-claimed verification statements.

Usage:
    python lint_claims.py docs/agent/STATE.md [other.md ...]

A line that claims something is verified/working/fixed must carry one of the labels
[SCRIPTED], [PIE-SIMULATED], [HUMAN-NEEDED] on the same line, or sit under a heading
that carries one. Claims about things only a human can judge (real keyboard/mouse,
lighting, looks, sound, feel) must be labeled [HUMAN-NEEDED].

Exit code: 0 = no findings, 1 = findings, 2 = bad usage.
This is a review aid, not a proof. Findings need a human or agent decision.
"""
import re
import sys
from pathlib import Path

LABELS = ("[SCRIPTED]", "[PIE-SIMULATED]", "[HUMAN-NEEDED]")

CLAIM = re.compile(
    r"\b(verified|confirmed|passed|passes|passing|works|working|fixed|validated|clean|correct)\b",
    re.IGNORECASE,
)
# Negated or hedged statements are not claims.
NEGATION = re.compile(
    r"\b(not|never|cannot|can't|unverified|unproven|untested|unconfirmed|chưa|không)\b",
    re.IGNORECASE,
)
# Things the agent cannot judge by itself on this project (it cannot see, hear or press keys).
HUMAN_ONLY = re.compile(
    r"\b(keyboard|mouse|gamepad|controller|real input|lighting|visual|visually|looks?|"
    r"readable|readability|sounds?|audio|hear|heard|screenshot|feel|fun|scary|atmosphere)\b",
    re.IGNORECASE,
)


def labels_in(text: str):
    return [label for label in LABELS if label in text]


def lint_file(path: Path):
    findings = []
    in_fence = False
    heading = ""
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if line.startswith("#"):
            heading = line
            continue
        if not CLAIM.search(line) or NEGATION.search(line):
            continue
        labels = labels_in(line) or labels_in(heading)
        if not labels:
            findings.append((number, "UNLABELED_CLAIM", line))
        elif HUMAN_ONLY.search(line) and "[HUMAN-NEEDED]" not in labels:
            findings.append((number, "HUMAN_ONLY_CLAIM", line))
    return findings


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for name in argv[1:]:
        path = Path(name)
        if not path.is_file():
            print(f"{name}: not a file")
            total += 1
            continue
        for number, code, text in lint_file(path):
            snippet = text if len(text) <= 140 else text[:137] + "..."
            print(f"{name}:{number}: {code}: {snippet}")
            total += 1
    print(f"{total} finding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
