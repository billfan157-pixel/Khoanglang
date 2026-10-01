#!/usr/bin/env python3
"""Validate Khoảng Lặng story data outside Unreal.

Usage:
    python validate_story_data.py data/story            # development check
    python validate_story_data.py data/story --release  # prototype_only entries become errors

Expected files in the data directory (JSON arrays; knowledge.json is an object):
    truths.json     [{id, summary, reveal_chapter, canon_ref}]
    clues.json      [{id, truth, chapter, canon_ref, prototype_only?}]
    sources.json    [{id, kind, chapter_available, canon_ref, prototype_only?}]
    puzzles.json    [{id, chapter, sources:[source ids], canon_ref}]
    knowledge.json  {"learns":[{npc, truth, chapter}], "uses":[{npc, truth, chapter, ref}]}

See ../references/schema.md for the meaning of each field.
The thresholds below mirror the V3 rules as summarized in project notes. Confirm them
against the canon (V3 section 8.2 and the clue-seeding table) and change the constants
here if the canon says otherwise.

Exit code: 0 = no errors, 1 = errors, 2 = bad usage.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

MIN_CLUES_BEFORE_REVEAL = 2   # clues per truth that must appear BEFORE its reveal chapter
CLUE_LEAD_CHAPTERS = 1        # "before" means at least this many chapters earlier
MIN_SOURCES_PER_PUZZLE = 2    # sources needed to seal a cut sentence
REQUIRED_KIND = "independent" # at least one source of this kind per puzzle
VALID_KINDS = {"independent", "related", "interested"}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append(f"ERROR {where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"WARN  {where}: {message}")


def load(directory: Path, name: str, report: Report, required=True):
    path = directory / name
    if not path.is_file():
        (report.error if required else report.warn)(name, "file not found")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report.error(name, f"cannot read as UTF-8 JSON: {exc}")
        return None


def index_by_id(items, filename, required_fields, report):
    result = {}
    if items is None:
        return result
    if not isinstance(items, list):
        report.error(filename, "top level must be a JSON array")
        return result
    for position, item in enumerate(items):
        where = f"{filename}[{position}]"
        if not isinstance(item, dict):
            report.error(where, "entry must be an object")
            continue
        for field in required_fields:
            if field not in item:
                report.error(where, f"missing field '{field}'")
        item_id = item.get("id")
        if item_id is None:
            continue
        if item_id in result:
            report.error(where, f"duplicate id '{item_id}'")
        result[item_id] = item
    return result


def check_provenance(entries, filename, release, report):
    for item_id, item in entries.items():
        where = f"{filename}:{item_id}"
        if not item.get("canon_ref"):
            report.warn(where, "no canon_ref - is this invented content?")
        if item.get("prototype_only"):
            (report.error if release else report.warn)(
                where, "prototype_only entry" + (" blocks release" if release else " (must be replaced before vertical slice)")
            )


def validate(directory: Path, release: bool) -> Report:
    report = Report()
    truths = index_by_id(load(directory, "truths.json", report), "truths.json",
                         ["id", "reveal_chapter"], report)
    clues = index_by_id(load(directory, "clues.json", report), "clues.json",
                        ["id", "truth", "chapter"], report)
    sources = index_by_id(load(directory, "sources.json", report), "sources.json",
                          ["id", "kind", "chapter_available"], report)
    puzzles = index_by_id(load(directory, "puzzles.json", report), "puzzles.json",
                          ["id", "chapter", "sources"], report)
    knowledge = load(directory, "knowledge.json", report, required=False) or {}

    for name, entries in (("truths.json", truths), ("clues.json", clues),
                          ("sources.json", sources), ("puzzles.json", puzzles)):
        check_provenance(entries, name, release, report)

    # Rule 1: every truth is seeded by enough earlier clues.
    clues_by_truth = defaultdict(list)
    for clue_id, clue in clues.items():
        truth_id = clue.get("truth")
        if truth_id not in truths:
            report.error(f"clues.json:{clue_id}", f"unknown truth '{truth_id}'")
            continue
        clues_by_truth[truth_id].append(clue)
    for truth_id, truth in truths.items():
        reveal = truth.get("reveal_chapter")
        if not isinstance(reveal, int):
            report.error(f"truths.json:{truth_id}", "reveal_chapter must be an integer")
            continue
        early = [c for c in clues_by_truth[truth_id]
                 if isinstance(c.get("chapter"), int) and c["chapter"] <= reveal - CLUE_LEAD_CHAPTERS]
        if len(early) < MIN_CLUES_BEFORE_REVEAL:
            report.error(
                f"truths.json:{truth_id}",
                f"only {len(early)} clue(s) seeded at least {CLUE_LEAD_CHAPTERS} chapter(s) before "
                f"reveal in chapter {reveal}; need {MIN_CLUES_BEFORE_REVEAL}",
            )

    # Rule 2: sealing puzzles need enough sources, including an independent one.
    for source_id, source in sources.items():
        if source.get("kind") not in VALID_KINDS:
            report.error(f"sources.json:{source_id}",
                         f"kind must be one of {sorted(VALID_KINDS)}, got '{source.get('kind')}'")
    for puzzle_id, puzzle in puzzles.items():
        where = f"puzzles.json:{puzzle_id}"
        listed = puzzle.get("sources") or []
        known = []
        for source_id in listed:
            source = sources.get(source_id)
            if source is None:
                report.error(where, f"unknown source '{source_id}'")
                continue
            known.append(source)
            available = source.get("chapter_available")
            if isinstance(available, int) and isinstance(puzzle.get("chapter"), int) \
                    and available > puzzle["chapter"]:
                report.error(where, f"source '{source_id}' is only available from chapter "
                                    f"{available}, after puzzle chapter {puzzle['chapter']}")
        if len(known) < MIN_SOURCES_PER_PUZZLE:
            report.error(where, f"{len(known)} source(s); need at least {MIN_SOURCES_PER_PUZZLE}")
        if not any(s.get("kind") == REQUIRED_KIND for s in known):
            report.error(where, f"no '{REQUIRED_KIND}' source among the puzzle's sources")

    # Rule 3: nobody uses a fact before they learned it.
    learned = defaultdict(dict)  # (npc) -> {truth: earliest chapter}
    for entry in knowledge.get("learns", []):
        npc, truth, chapter = entry.get("npc"), entry.get("truth"), entry.get("chapter")
        if truth not in truths:
            report.error("knowledge.json:learns", f"{npc}: unknown truth '{truth}'")
            continue
        previous = learned[npc].get(truth)
        if previous is None or (isinstance(chapter, int) and chapter < previous):
            learned[npc][truth] = chapter
    for entry in knowledge.get("uses", []):
        npc, truth, chapter = entry.get("npc"), entry.get("truth"), entry.get("chapter")
        where = f"knowledge.json:uses {npc}/{truth}"
        if truth not in truths:
            report.error(where, f"unknown truth '{truth}'")
            continue
        first = learned.get(npc, {}).get(truth)
        if first is None:
            report.error(where, f"used in chapter {chapter} but {npc} never learns it")
        elif isinstance(chapter, int) and isinstance(first, int) and chapter < first:
            report.error(where, f"used in chapter {chapter} but only learned in chapter {first}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Validate story data (see module docstring).")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--release", action="store_true",
                        help="treat prototype_only entries as errors")
    args = parser.parse_args()
    if not args.directory.is_dir():
        print(f"not a directory: {args.directory}")
        return 2
    report = validate(args.directory, args.release)
    for line in report.errors + report.warnings:
        print(line)
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
