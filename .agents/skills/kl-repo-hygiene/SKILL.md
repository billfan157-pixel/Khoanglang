---
name: kl-repo-hygiene
description: Git, Git LFS, and file-safety rules for the Khoảng Lặng Unreal repo - preflight report, commit grouping, tagging before risky edits, one writer per map or asset area, generator scripts that can overwrite hand edits, and keeping machine paths and secrets out of a public repo. Use this skill before any commit, push, tag, or branch; before editing a map or Blueprint; before running a generator or build script; when git status shows many changes; when two maps or assets look like competing versions; and when adding new file types or documentation to the repo.
---

# Repository hygiene

Unreal maps and Blueprints are binary: git cannot merge them and cannot show what changed. The only protection is discipline about when state is saved and who is allowed to write. Several things have already gone wrong here: about 96 uncommitted items at once, competing map versions (`Merged`, `Primary`, `ArtTest`), an asset modified by concurrent work, and generator scripts that can overwrite hand edits.

## Preflight (read-only)

Run before starting a task and again before committing:

```
python .agents/skills/kl-repo-hygiene/scripts/git_preflight.py
```

It reports uncommitted changes by area, changed `.uasset` / `.umap` files, Git LFS coverage gaps, large files that are not LFS pointers, and machine-specific paths or secrets in text files. It changes nothing. Exit 1 means there are warnings to read; it is not a reason to stop, but do not commit new problems on top.

## Commit rules

- Group commits by kind: code and scripts, story data, maps, assets, docs. One logical change per commit, with a message that says what and why.
- Never commit `Saved/`, `Intermediate/`, `Binaries/`, `DerivedDataCache/`, or agent artifacts.
- Commit (or tag) the working state before any Blueprint or map edit, and before running any generator. Tag stable points, for example `prototype-baseline`. The MCP has no undo, so git is the undo.
- Show the developer the commit list and wait for approval before the first big cleanup commit. Never force-push, rewrite history, or push without explicit confirmation.

## Git LFS

`.gitattributes` must send these to LFS: `.uasset .umap .blend .fbx .png .jpg .tga .wav .ogg .mp3 .flac .exr .hdr .psd`. The game is audio-driven, so audio formats matter most. Add missing patterns before the first file of that type is committed; a binary committed as a plain blob stays in history. The preflight lists gaps. The repo is on GitHub, whose LFS storage and bandwidth quotas are limited, so keep raw captures, recordings and snapshots out of the repo.

## One writer per area

- Only one agent or person edits a given map or asset area at a time. Before touching a map, say which map you will edit and wait if anything suggests another session is using it (for example a second editor process).
- Before opening or saving a map, ask which map is canonical when more than one candidate exists, and compare file timestamps with git history rather than guessing.
- Never save a map or asset that was changed on disk after it was loaded into the editor; reload it instead (`kl-unreal-mcp-ops`).
- Safety snapshots (`_recovery_*` copies) do not belong in `Content/`. Use a git tag, or keep them outside the repo.
- Prefer separating work into sublevels (gameplay, props and art, lighting) so art and gameplay edits stop colliding in one `.umap`. Propose the split; do not migrate maps without approval.

## Generators and build scripts

Scripts in `Content/Python/KhoangLang/` and `tools/` generate Blueprints, levels and meshes. Keep `tools/README.md` with one line per script: GENERATOR or VERIFIER, what it overwrites, and when it was last run. A generator must refuse to overwrite an asset modified after the generator last produced it unless a `--force` flag is passed. Before running one, check timestamps and commit first. Fix bugs in the generator and in the generated asset together, and note which is the source of truth.

## Public repo hygiene

The repository is public. Unreleased story, plot twists and assets are visible, and the license of third-party assets (for example Fab or Marketplace packs) often forbids redistributing the raw files. Raise this with the developer before adding third-party assets; suggesting a private repository is reasonable.

Keep out of tracked files: absolute paths (`C:\Users\...`, `C:\Program Files\...`), hardware or personal details, API keys, tokens, `opencode.jsonc` contents that include credentials. Machine-specific notes go in a gitignored local file such as `docs/local/MACHINE.md`. The preflight scans for these patterns.
