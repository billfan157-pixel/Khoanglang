#!/usr/bin/env python3
"""Preflight report for the Khoảng Lặng repository. Read-only: it never changes anything.

Usage:
    python git_preflight.py [--repo PATH] [--max-mb 5]

Reports:
    * current branch, latest tag, and the uncommitted changes grouped by area and kind
    * Git LFS coverage: binary extensions that .gitattributes does not send to LFS
    * large files (> --max-mb) that are neither LFS pointers nor ignored
    * tracked or untracked text files that leak machine-specific absolute paths or secrets
    * modified or untracked Unreal binary assets (.uasset/.umap), which cannot be merged

It parses .gitattributes itself and does not need the git-lfs executable.
Exit code: 0 = no warnings, 1 = warnings found, 2 = not a git repository.
"""
import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REQUIRED_LFS_EXTENSIONS = [
    ".uasset", ".umap", ".blend", ".fbx", ".png", ".jpg", ".tga",
    ".wav", ".ogg", ".mp3", ".flac", ".exr", ".hdr", ".psd",
]
BINARY_ASSETS = {".uasset", ".umap"}
TEXT_EXTENSIONS = {".md", ".py", ".json", ".jsonc", ".ps1", ".txt", ".ini", ".yaml", ".yml", ".cfg"}
PRIVACY_PATTERNS = [
    ("ABSOLUTE_PATH", re.compile(r"[A-Za-z]:\\(?:Users|Program Files)")),
    ("SECRET", re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}")),
    ("KEY_LITERAL", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
]
LFS_POINTER_PREFIX = b"version https://git-lfs"
LFS_POINTER_PREFIX_TEXT = LFS_POINTER_PREFIX.decode("ascii")


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return result.returncode, result.stdout


def lfs_extensions(repo):
    covered = set()
    attributes = repo / ".gitattributes"
    if attributes.is_file():
        for line in attributes.read_text(encoding="utf-8", errors="replace").splitlines():
            if "filter=lfs" in line:
                pattern = line.split()[0]
                match = re.fullmatch(r"\*(\.[A-Za-z0-9]+)", pattern)
                if match:
                    covered.add(match.group(1).lower())
    return covered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--max-mb", type=float, default=5.0)
    args = parser.parse_args()
    repo = args.repo.resolve()

    code, top = git(repo, "rev-parse", "--show-toplevel")
    if code != 0:
        print("not a git repository")
        return 2
    repo = Path(top.strip())
    warnings = 0

    _, branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _, tag = git(repo, "describe", "--tags", "--abbrev=0")
    print(f"branch: {branch.strip() or '(none)'}   latest tag: {tag.strip() or '(none)'}")

    # Working-tree changes.
    _, status = git(repo, "status", "--porcelain", "-uall")
    changed = []
    for line in status.splitlines():
        if len(line) > 3:
            changed.append((line[:2].strip() or "?", line[3:].strip().strip('"')))
    print(f"\nuncommitted items: {len(changed)}")
    by_area = Counter(path.split("/")[0] for _, path in changed)
    for area, count in by_area.most_common():
        print(f"  {area}: {count}")
    binaries = [path for _, path in changed if Path(path).suffix.lower() in BINARY_ASSETS]
    if binaries:
        warnings += 1
        print(f"\nWARN {len(binaries)} Unreal binary asset(s) changed - they cannot be merged; "
              f"commit them before any further edit and keep one writer per asset area:")
        for path in binaries[:10]:
            print(f"  {path}")
        if len(binaries) > 10:
            print(f"  ... and {len(binaries) - 10} more")

    # LFS coverage.
    covered = lfs_extensions(repo)
    missing = [ext for ext in REQUIRED_LFS_EXTENSIONS if ext not in covered]
    if missing:
        warnings += 1
        print(f"\nWARN .gitattributes does not send these extensions to LFS: {' '.join(missing)}")
    else:
        print("\nLFS coverage: all required extensions are covered")

    # Files to inspect = tracked + untracked-not-ignored.
    _, tracked = git(repo, "ls-files")
    _, untracked = git(repo, "ls-files", "--others", "--exclude-standard")
    files = [f for f in (tracked.splitlines() + untracked.splitlines()) if f]

    large = []
    uncovered_binaries = []
    for name in files:
        path = repo / name
        if not path.is_file():
            continue
        size = path.stat().st_size
        with path.open("rb") as handle:
            head = handle.read(64)
        # Ask git what it actually stores, not what is on disk. After an LFS
        # checkout the worktree holds smudged real content while the repository
        # holds a pointer, so reading the worktree reports every LFS file as a
        # plain blob.
        is_pointer = head.startswith(LFS_POINTER_PREFIX)
        code, stored = git(repo, "cat-file", "-p", f"HEAD:{name}")
        if code == 0:
            is_pointer = stored.startswith(LFS_POINTER_PREFIX_TEXT)
        if size > args.max_mb * 1024 * 1024 and not is_pointer:
            large.append((name, size))
        suffix = path.suffix.lower()
        if suffix in REQUIRED_LFS_EXTENSIONS and suffix in covered and not is_pointer and size > 1024:
            uncovered_binaries.append(name)
    if large:
        warnings += 1
        print(f"\nWARN {len(large)} file(s) over {args.max_mb:g} MB that are not LFS pointers:")
        for name, size in large[:10]:
            print(f"  {name} ({size / 1024 / 1024:.1f} MB)")
    if uncovered_binaries:
        warnings += 1
        print(f"\nWARN {len(uncovered_binaries)} binary file(s) match an LFS pattern but are stored "
              f"as plain blobs (added before LFS was set up?):")
        for name in uncovered_binaries[:10]:
            print(f"  {name}")

    # Privacy scan of text files outside Content/.
    leaks = []
    for name in files:
        path = repo / name
        if path.suffix.lower() not in TEXT_EXTENSIONS or name.startswith("Content/") or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            for label, pattern in PRIVACY_PATTERNS:
                if pattern.search(line):
                    leaks.append((name, number, label))
    if leaks:
        warnings += 1
        print(f"\nWARN {len(leaks)} possible machine-specific path or secret leak(s) in text files:")
        for name, number, label in leaks[:15]:
            print(f"  {name}:{number}: {label}")
        if len(leaks) > 15:
            print(f"  ... and {len(leaks) - 15} more")

    print(f"\n{warnings} warning group(s)")
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
