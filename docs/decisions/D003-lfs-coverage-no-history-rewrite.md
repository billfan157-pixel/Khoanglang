# D003 — LFS coverage gap: add patterns, do not rewrite history

Date: 2026-10-01. Decided by the agent during Task 2.0 skill setup; the
history-rewrite half is left to the project owner.

## Context

`git_preflight.py` reported that `.gitattributes` did not send seven required
extensions to Git LFS: `.ogg .mp3 .flac .exr .hdr .psd`. The project is
audio-driven (environmental audio plus the T1/T2/T3 tapes), so audio formats
matter more than the rest.

It also reported that 492 binary files already in history match an LFS pattern
but are stored as plain blobs, and that one file is over 5 MB without being an
LFS pointer (`docs/agent/EVIDENCE/G1_merged_editor_runtime.log`, 55.3 MB).

## Decision

1. **Add the seven missing patterns to `.gitattributes`.** Cheap, forward-only,
   no history change. `git_preflight.py` now reports "LFS coverage: all
   required extensions are covered" [SCRIPTED].
2. **Do not run `git lfs migrate import` on this repository.** It rewrites every
   commit, changes every commit hash, and would invalidate the review checkout
   `KhoangLang0217-g1-review-8220edf` and the checkpoint references in
   `docs/agent/STATE.md` (`8220edf`, `439582a2...`). It also pushes the repo
   toward GitHub's LFS storage and bandwidth quotas, which `kl-repo-hygiene`
   warns are limited. Rewriting history is not an agent decision
   (`kl-repo-hygiene`: never force-push or rewrite history without explicit
   confirmation).

## Known debt, accepted for now

- 492 binary blobs stay as plain blobs in history. Current checkouts are
  unaffected; the cost is repository size and slower clones.
- `G1_merged_editor_runtime.log` (55.3 MB) stays tracked as a plain blob. It is
  editor evidence, already committed, and rewriting it means rewriting history.
  [SCRIPTED] The file exists and is 55.3 MB.

## Revisit when

- The repository moves to a private host with room for LFS, or
- the clone size becomes painful, or
- the project owner explicitly asks for the migration and accepts new commit
  hashes and the cost of re-cloning every checkout.